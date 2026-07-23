"""
REST API routes for the evaluation pipeline.

POST /api/v1/evaluate          — async, returns job_id
GET  /api/v1/status/{job_id}   — poll job status
GET  /api/v1/result/{job_id}   — retrieve finished result
POST /api/v1/evaluate/sync     — synchronous (dev/debug only, requires secret key)
GET  /api/v1/health            — liveness check
GET  /api/v1/document/{job_id}      — serve original uploaded file
GET  /api/v1/document/{job_id}/meta — file type, name, page count
GET  /api/v1/document/{job_id}/html — HTML rendering for DOCX/TXT preview
"""

import logging
import uuid
import secrets
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response

from app.config import get_settings
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.document_service import DocumentService
from app.utils.job_store import job_store
from app.utils.file_store import file_store

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
        content = await file.read()
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


@router.post("/evaluate", summary="Submit document for asynchronous evaluation")
async def evaluate(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
):
    text, pages, file_bytes, content_type, filename = await _resolve_text_and_meta(file, raw_text)
    job_id = str(uuid.uuid4())
    source = filename or "raw_text"
    logger.info("Evaluate request — job_id=%s  source=%r  doc_len=%d chars", job_id, source, len(text))

    if file_bytes is not None:
        file_store.save(job_id, file_bytes, content_type, filename, pages)

    job_store.create(job_id, status="queued", stage="pending", progress=0)
    background_tasks.add_task(orchestrator.run, job_id, text, pages)
    return {"job_id": job_id, "status": "queued"}


@router.get("/status/{job_id}", summary="Poll evaluation job status")
async def get_status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found.")
    return {
        "job_id": job["job_id"],
        "status": job.get("status", "unknown"),
        "stage": job.get("stage", ""),
        "progress": job.get("progress", 0),
        "error": job.get("error"),
    }


@router.get("/result/{job_id}", summary="Retrieve completed evaluation result")
async def get_result(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found.")
    if job.get("status") == "failed":
        raise HTTPException(500, f"Evaluation failed: {job.get('error', 'unknown error')}")
    if job.get("status") != "complete":
        raise HTTPException(202, "Evaluation not complete yet. Poll /status for progress.")

    result = job_store.get_result(job_id)
    if result is None:
        raise HTTPException(500, "Result record missing despite complete status.")
    return result


@router.post(
    "/evaluate/sync",
    summary="Synchronous evaluation (development / secret-key protected)",
)
async def evaluate_sync(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    x_secret_key: Optional[str] = Form(None),
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
    job_id = str(uuid.uuid4())
    source = filename or "raw_text"
    logger.info("Evaluate/sync request — job_id=%s  source=%r  doc_len=%d chars", job_id, source, len(text))

    if file_bytes is not None:
        file_store.save(job_id, file_bytes, content_type, filename, pages)

    job_store.create(job_id, status="queued", stage="pending", progress=0)

    try:
        result = await orchestrator.run(job_id, text, pages)
        return result
    except Exception as exc:
        logger.exception("Evaluate/sync — pipeline error for job_id=%s", job_id)
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


# ── Document preview endpoints ─────────────────────────────────────────────────

@router.get("/document/{job_id}/meta", summary="Document metadata for preview")
async def document_meta(job_id: str):
    meta = file_store.get_meta(job_id)
    if meta is None:
        raise HTTPException(404, "No document stored for this job (text-input evaluation).")
    return meta


@router.get("/document/{job_id}", summary="Serve original uploaded document")
async def document_file(job_id: str):
    result = file_store.get_content(job_id)
    if result is None:
        raise HTTPException(404, "No document stored for this job.")
    content, content_type = result
    return Response(content=content, media_type=content_type)


@router.get("/document/{job_id}/html", summary="HTML rendering of document for preview")
async def document_html(job_id: str):
    result = file_store.get_content(job_id)
    if result is None:
        raise HTTPException(404, "No document stored for this job.")
    content, _ = result
    meta = file_store.get_meta(job_id)
    filename = meta["filename"] if meta else "document.txt"
    html_str = doc_service.to_html(content, filename)
    return HTMLResponse(content=html_str)
