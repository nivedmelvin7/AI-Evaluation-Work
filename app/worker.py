"""Durable PostgreSQL-backed worker for queued evaluation jobs."""

import asyncio
import logging
import os
import signal
import socket
import uuid
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.logging_config import setup_logging
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services import session_service

logger = logging.getLogger(__name__)


async def _recover_stale_jobs() -> None:
    settings = get_settings()
    stale_before = datetime.now(timezone.utc) - timedelta(
        seconds=settings.worker_stale_after_seconds
    )
    async with AsyncSessionLocal() as db:
        requeued, failed = await session_service.recover_stale_versions(
            db,
            stale_before=stale_before,
            max_attempts=settings.worker_max_attempts,
        )
    if requeued or failed:
        logger.warning("Recovered stale jobs: requeued=%d failed=%d", requeued, failed)


async def _claim_next_job(worker_id: str):
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        return await session_service.claim_next_queued_version(
            db,
            worker_id=worker_id,
            max_attempts=settings.worker_max_attempts,
        )


async def _record_failure(version_id: uuid.UUID, error: Exception) -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        await session_service.retry_or_fail_version(
            db,
            version_id,
            max_attempts=settings.worker_max_attempts,
            error=str(error),
        )


async def run_worker() -> None:
    settings = get_settings()
    setup_logging(debug=settings.app_debug, log_to_file=settings.log_to_file)
    worker_id = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
    orchestrator = PipelineOrchestrator()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for signal_name in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signal_name, stop_event.set)
        except (NotImplementedError, RuntimeError):
            # Windows uses the default KeyboardInterrupt path; Linux containers
            # install these handlers for graceful Docker shutdown.
            pass

    logger.info("Evaluation worker started: worker_id=%s", worker_id)
    await _recover_stale_jobs()
    stale_recovery_interval = max(
        30.0,
        min(300.0, settings.worker_stale_after_seconds / 2),
    )
    next_stale_recovery = loop.time() + stale_recovery_interval

    while not stop_event.is_set():
        try:
            if loop.time() >= next_stale_recovery:
                await _recover_stale_jobs()
                next_stale_recovery = loop.time() + stale_recovery_interval

            job = await _claim_next_job(worker_id)
            if job is None:
                try:
                    await asyncio.wait_for(
                        stop_event.wait(), timeout=settings.worker_poll_seconds
                    )
                except asyncio.TimeoutError:
                    pass
                continue

            logger.info(
                "Claimed evaluation job: job_id=%s attempt=%d",
                job.version_id,
                job.attempt_count,
            )
            try:
                await orchestrator.run(
                    job.version_id,
                    job.document_text,
                    job.pages,
                    mark_failed=False,
                )
            except Exception as exc:
                logger.exception("Evaluation job failed: job_id=%s", job.version_id)
                await _record_failure(job.version_id, exc)
        except Exception:
            logger.exception("Worker loop error")
            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=settings.worker_poll_seconds
                )
            except asyncio.TimeoutError:
                pass

    logger.info("Evaluation worker stopped: worker_id=%s", worker_id)


if __name__ == "__main__":
    asyncio.run(run_worker())
