"""
REST API routes for the evaluation pipeline.

POST /api/v1/evaluate          — async, returns job_id
GET  /api/v1/status/{job_id}   — poll job status
GET  /api/v1/result/{job_id}   — retrieve finished result
POST /api/v1/evaluate/sync     — synchronous (dev/debug only, requires secret key)
GET  /api/v1/health            — liveness check
"""

import uuid
import secrets
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.document_service import DocumentService
from app.utils.job_store import job_store

router = APIRouter(prefix="/api/v1")
orchestrator = PipelineOrchestrator()
doc_service = DocumentService()


def _parse_upload(file: Optional[UploadFile], raw_text: Optional[str]) -> tuple[str, str]:
    """Validate that exactly one source is provided; return (text, source_description)."""
    if file is None and raw_text is None:
        raise HTTPException(400, "Provide either a file or raw_text.")
    return None, None  # actual parsing done after await


async def _resolve_text(file: Optional[UploadFile], raw_text: Optional[str]) -> str:
    """Parse file or accept raw text, enforcing the character limit."""
    settings = get_settings()

    if file is not None:
        content = await file.read()
        try:
            text = doc_service.parse_file(content, file.filename)
        except ValueError as e:
            raise HTTPException(400, str(e))
    elif raw_text is not None:
        text = raw_text
    else:
        raise HTTPException(400, "Provide either a file or raw_text.")

    if len(text) > settings.max_document_chars:
        raise HTTPException(
            413,
            f"Document exceeds maximum of {settings.max_document_chars:,} characters."
        )
    if len(text.strip()) == 0:
        raise HTTPException(400, "Document text is empty.")

    return text


@router.post("/evaluate", summary="Submit document for asynchronous evaluation")
async def evaluate(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
):
    """
    Accept a document and queue it for evaluation.
    Returns immediately with a job_id to poll for status/result.
    """
    text = await _resolve_text(file, raw_text)
    job_id = str(uuid.uuid4())
    job_store.create(job_id, status="queued", stage="pending", progress=0)
    background_tasks.add_task(orchestrator.run, job_id, text)
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
    """
    Runs the full pipeline synchronously and returns the result directly.
    Requires the SECRET_KEY from .env to prevent accidental production use.
    """
    settings = get_settings()

    # Protect in production: require secret key unless debug mode is on
    if not settings.app_debug:
        if x_secret_key is None or not secrets.compare_digest(x_secret_key, settings.secret_key):
            raise HTTPException(
                403,
                "Synchronous endpoint requires x_secret_key form field matching SECRET_KEY, "
                "or APP_DEBUG=true in .env."
            )

    text = await _resolve_text(file, raw_text)
    job_id = str(uuid.uuid4())
    job_store.create(job_id, status="queued", stage="pending", progress=0)

    try:
        result = await orchestrator.run(job_id, text)
        return result
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {e}")


@router.get("/health", summary="Liveness check")
async def health():
    settings = get_settings()
    model = (
        settings.groq_primary_model
        if settings.llm_backend == "groq"
        else settings.ollama_primary_model
    )
    return {
        "status": "ok",
        "backend": settings.llm_backend,
        "model": model,
        "debug": settings.app_debug,
    }
