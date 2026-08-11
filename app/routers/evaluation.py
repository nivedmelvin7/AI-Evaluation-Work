"""
REST API routes for the evaluation pipeline.

POST /api/v1/evaluate               — async, returns session_id + job_id
GET  /api/v1/status/{job_id}        — poll job status
GET  /api/v1/result/{job_id}        — retrieve finished result
POST /api/v1/evaluate/sync          — synchronous (dev/debug only, requires secret key)
GET  /api/v1/health                 — liveness check
GET  /api/v1/document/{job_id}      — serve original uploaded file
GET  /api/v1/document/{job_id}/meta — file type, name, page count
GET  /api/v1/document/{job_id}/html — HTML rendering for DOCX/TXT preview

GET    /api/v1/sessions                     — list evaluation sessions (history drawer)
GET    /api/v1/sessions/{session_id}        — session detail + all versions
POST   /api/v1/sessions/{session_id}/reevaluate — re-run the pipeline, keeping prior versions
DELETE /api/v1/sessions/{session_id}        — archive (soft delete, never destroys history)
POST   /api/v1/sessions/{session_id}/unarchive  — restore an archived session
"""

import logging
import secrets
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import text as sql_text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services import session_service
from app.services.document_service import DocumentService
from app.security.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")
orchestrator = PipelineOrchestrator()
doc_service = DocumentService()

_CONTENT_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".txt": "text/plain; charset=utf-8",
}

_UPLOAD_READ_CHUNK_BYTES = 1024 * 1024


def _parse_uuid(value: str, label: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(400, f"Invalid {label} '{value}'.")


def _version_summary(version) -> dict:
    return {
        "job_id": str(version.id),
        "version_number": version.version_number,
        "is_current": version.is_current,
        "status": version.status,
        "stage": version.stage,
        "progress": version.progress,
        "error": version.error,
        "final_score": version.final_score,
        "grade_band": version.grade_band,
        "created_at": version.created_at.isoformat() if version.created_at else None,
        "completed_at": version.completed_at.isoformat() if version.completed_at else None,
    }


def _session_summary(session_row) -> dict:
    versions = sorted(session_row.versions, key=lambda v: v.version_number)
    latest = versions[-1] if versions else None
    return {
        "session_id": str(session_row.id),
        "filename": session_row.filename,
        "content_type": session_row.content_type,
        "created_at": session_row.created_at.isoformat() if session_row.created_at else None,
        "updated_at": session_row.updated_at.isoformat() if session_row.updated_at else None,
        "archived": session_row.archived_at is not None,
        "version_count": len(versions),
        "latest": _version_summary(latest) if latest else None,
    }


async def _resolve_text_and_meta(
    file: Optional[UploadFile],
    raw_text: Optional[str],
) -> tuple:
    """
    Returns (text, pages, file_bytes, content_type, filename).
    pages is None when input is raw text.
    """
    settings = get_settings()

    if file is not None:
        content = await _read_upload_limited(file, settings.max_upload_bytes)
        try:
            parsed = doc_service.parse_file_with_pages(content, file.filename)
        except ValueError as e:
            raise HTTPException(400, str(e))
        text = parsed["text"]
        pages = parsed["pages"]
        from pathlib import Path
        ext = Path(file.filename).suffix.lower()
        content_type = _CONTENT_TYPE_MAP.get(ext, "application/octet-stream")
        file_bytes = content
        filename = file.filename
    elif raw_text is not None:
        text = raw_text
        pages = None
        file_bytes = None
        content_type = None
        filename = None
    else:
        raise HTTPException(400, "Provide either a file or raw_text.")

    if len(text) > settings.max_document_chars:
        raise HTTPException(
            413,
            f"Document exceeds maximum of {settings.max_document_chars:,} characters.",
        )
    if len(text.strip()) == 0:
        raise HTTPException(400, "Document text is empty.")

    return text, pages, file_bytes, content_type, filename


async def _read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    """Read at most ``max_bytes`` plus one sentinel byte from an upload."""
    content = bytearray()
    while True:
        remaining_with_sentinel = max_bytes + 1 - len(content)
        chunk = await file.read(min(_UPLOAD_READ_CHUNK_BYTES, remaining_with_sentinel))
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_bytes:
            limit_mib = max_bytes / (1024 * 1024)
            raise HTTPException(413, f"Uploaded file exceeds the {limit_mib:g} MiB limit.")
    return bytes(content)


async def _run_pipeline_background(version_id: uuid.UUID, text: str, pages: Optional[list]):
    """Background-task entrypoint — the orchestrator opens its own DB session
    since the request (and its session) is already gone by the time this runs."""
    await orchestrator.run(version_id, text, pages)


@router.post("/evaluate", summary="Submit document for asynchronous evaluation")
async def evaluate(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text, pages, file_bytes, content_type, filename = await _resolve_text_and_meta(file, raw_text)
    source = filename or "raw_text"
    doc_hash = session_service.hash_document(file_bytes, text)

    existing_session = await session_service.find_session_by_document_hash(db, doc_hash, current_user.id)
    if existing_session is not None:
        # Same document already evaluated before (byte-identical re-upload) —
        # nest this run as a new version under the existing session/folder
        # instead of creating a duplicate one.
        session_row = existing_session
        version = await session_service.create_reevaluation(db, session_row.id, current_user.id)
        logger.info(
            "Evaluate request — matched existing session_id=%s by content hash, "
            "job_id=%s source=%r version=%d",
            session_row.id, version.id, source, version.version_number,
        )
    else:
        session_row, version = await session_service.create_session(
            db,
            document_text=text,
            owner_id=current_user.id,
            filename=filename,
            content_type=content_type,
            content=file_bytes,
            pages=pages,
        )
        logger.info(
            "Evaluate request — session_id=%s job_id=%s source=%r doc_len=%d chars",
            session_row.id, version.id, source, len(text),
        )

    background_tasks.add_task(_run_pipeline_background, version.id, text, pages)
    return {"session_id": str(session_row.id), "job_id": str(version.id), "status": "queued"}


@router.get("/status/{job_id}", summary="Poll evaluation job status")
async def get_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = await session_service.get_version(db, _parse_uuid(job_id, "job_id"), current_user.id)
    if not version:
        raise HTTPException(404, f"Job '{job_id}' not found.")
    return {
        "job_id": str(version.id),
        "session_id": str(version.session_id),
        "version_number": version.version_number,
        "status": version.status,
        "stage": version.stage,
        "progress": version.progress,
        "error": version.error,
    }


@router.get("/result/{job_id}", summary="Retrieve completed evaluation result")
async def get_result(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = await session_service.get_version(db, _parse_uuid(job_id, "job_id"), current_user.id)
    if not version:
        raise HTTPException(404, f"Job '{job_id}' not found.")
    if version.status == "failed":
        raise HTTPException(500, f"Evaluation failed: {version.error or 'unknown error'}")
    if version.status != "complete":
        raise HTTPException(202, "Evaluation not complete yet. Poll /status for progress.")
    if version.result_json is None:
        raise HTTPException(500, "Result record missing despite complete status.")
    return version.result_json


@router.post(
    "/evaluate/sync",
    summary="Synchronous evaluation (development / secret-key protected)",
)
async def evaluate_sync(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    x_secret_key: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()

    if not settings.app_debug:
        if x_secret_key is None or not secrets.compare_digest(x_secret_key, settings.secret_key):
            raise HTTPException(
                403,
                "Synchronous endpoint requires x_secret_key form field matching SECRET_KEY, "
                "or APP_DEBUG=true in .env.",
            )

    text, pages, file_bytes, content_type, filename = await _resolve_text_and_meta(file, raw_text)
    source = filename or "raw_text"

    session_row, version = await session_service.create_session(
        db,
        document_text=text,
        owner_id=current_user.id,
        filename=filename,
        content_type=content_type,
        content=file_bytes,
        pages=pages,
    )
    logger.info(
        "Evaluate/sync request — session_id=%s job_id=%s source=%r doc_len=%d chars",
        session_row.id, version.id, source, len(text),
    )

    try:
        result = await orchestrator.run(version.id, text, pages)
        return result
    except Exception as exc:
        logger.exception("Evaluate/sync — pipeline error for job_id=%s", version.id)
        raise HTTPException(500, f"Pipeline error: {exc}")


@router.get("/health", summary="Liveness check")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "backend": "openrouter",
        "model": settings.openrouter_model,
        "debug": settings.app_debug,
    }


@router.get("/health/ready", summary="Deployment readiness check")
async def readiness(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise HTTPException(503, "OpenRouter is not configured.")
    try:
        await db.execute(sql_text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Readiness check failed while connecting to PostgreSQL")
        raise HTTPException(503, "PostgreSQL is unavailable.")
    return {"status": "ready", "database": "ok", "openrouter": "configured"}


# ── Session history (drawer) endpoints ─────────────────────────────────────────

@router.get("/sessions", summary="List evaluation sessions")
async def list_sessions(
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = await session_service.list_sessions(
        db, include_archived=include_archived, limit=limit, offset=offset, owner_id=current_user.id
    )
    return {"sessions": [_session_summary(s) for s in sessions]}


@router.get("/sessions/{session_id}", summary="Session detail with full version history")
async def get_session_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_row = await session_service.get_session(
        db, _parse_uuid(session_id, "session_id"), current_user.id
    )
    if not session_row:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    versions = sorted(session_row.versions, key=lambda v: v.version_number)
    return {
        "session_id": str(session_row.id),
        "filename": session_row.filename,
        "content_type": session_row.content_type,
        "created_at": session_row.created_at.isoformat() if session_row.created_at else None,
        "updated_at": session_row.updated_at.isoformat() if session_row.updated_at else None,
        "archived": session_row.archived_at is not None,
        "versions": [_version_summary(v) for v in versions],
    }


@router.post("/sessions/{session_id}/reevaluate", summary="Re-run the pipeline for a session")
async def reevaluate_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sid = _parse_uuid(session_id, "session_id")
    try:
        version = await session_service.create_reevaluation(db, sid, current_user.id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))

    document = await session_service.get_document(db, sid)
    logger.info(
        "Re-evaluate request — session_id=%s job_id=%s version=%d",
        sid, version.id, version.version_number,
    )
    background_tasks.add_task(
        _run_pipeline_background, version.id, document.document_text, document.pages
    )
    return {
        "session_id": str(sid),
        "job_id": str(version.id),
        "version_number": version.version_number,
        "status": "queued",
    }


@router.delete("/sessions/{session_id}", summary="Archive a session (history is preserved)")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await session_service.archive_session(db, _parse_uuid(session_id, "session_id"), current_user.id)
    if not ok:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    return {"session_id": session_id, "archived": True}


@router.post("/sessions/{session_id}/unarchive", summary="Restore an archived session")
async def unarchive_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await session_service.unarchive_session(db, _parse_uuid(session_id, "session_id"), current_user.id)
    if not ok:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    return {"session_id": session_id, "archived": False}


# ── Document preview endpoints ─────────────────────────────────────────────────

@router.get("/document/{job_id}/meta", summary="Document metadata for preview")
async def document_meta(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = await session_service.get_document_for_version(
        db, _parse_uuid(job_id, "job_id"), current_user.id
    )
    if document is None or document.content is None:
        raise HTTPException(404, "No document stored for this job (text-input evaluation).")
    ct = document.content_type or ""
    if "pdf" in ct:
        file_type = "pdf"
    elif "openxmlformats" in ct or "msword" in ct or "docx" in ct or "doc" in ct:
        file_type = "docx"
    else:
        file_type = "txt"
    return {
        "type": file_type,
        "filename": document.filename,
        "num_pages": len(document.pages or []),
    }


@router.get("/document/{job_id}", summary="Serve original uploaded document")
async def document_file(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = await session_service.get_document_for_version(
        db, _parse_uuid(job_id, "job_id"), current_user.id
    )
    if document is None or document.content is None:
        raise HTTPException(404, "No document stored for this job.")
    return Response(content=document.content, media_type=document.content_type)


@router.get("/document/{job_id}/html", summary="HTML rendering of document for preview")
async def document_html(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = await session_service.get_document_for_version(
        db, _parse_uuid(job_id, "job_id"), current_user.id
    )
    if document is None or document.content is None:
        raise HTTPException(404, "No document stored for this job.")
    filename = document.filename or "document.txt"
    html_str = doc_service.to_html(document.content, filename)
    return HTMLResponse(content=html_str)
