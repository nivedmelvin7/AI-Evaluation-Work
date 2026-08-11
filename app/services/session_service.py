"""
Durable session/version persistence — replaces the old in-memory job_store
and file_store. A "session" is one submitted document; each pipeline run
against it (the original evaluation and every re-evaluation) is stored as
its own EvaluationVersion row. Versions are never deleted, so past analyses
always remain retrievable even after a re-evaluation produces a new one.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Document, EvaluationVersion, Session
from app.models.response_models import EvaluationResult


@dataclass(frozen=True)
class ClaimedEvaluation:
    version_id: uuid.UUID
    document_text: str
    pages: Optional[list]
    attempt_count: int


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sanitize_for_postgres(value: Any) -> Any:
    """Remove NUL characters from values destined for text or JSON columns.

    PostgreSQL rejects ``\\x00`` in UTF-8 text and JSONB values. PDF and DOCX
    extractors can occasionally emit it, so normalise extracted text and page
    metadata at the persistence boundary. Binary upload content is deliberately
    not passed to this helper: ``BYTEA`` supports NUL bytes and must retain the
    original file exactly.
    """
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, list):
        return [sanitize_for_postgres(item) for item in value]
    if isinstance(value, dict):
        return {
            sanitize_for_postgres(key) if isinstance(key, str) else key: sanitize_for_postgres(item)
            for key, item in value.items()
        }
    return value


def hash_document(content: Optional[bytes], document_text: str) -> str:
    """Content-identity hash for a submitted document. Uses the raw file
    bytes when available (uploads) so re-uploading the exact same file is
    detected regardless of how the text was extracted; falls back to the
    extracted text for pasted-text submissions, which have no file bytes."""
    if content is not None:
        return hashlib.sha256(content).hexdigest()
    return hashlib.sha256(sanitize_for_postgres(document_text).encode("utf-8")).hexdigest()


async def find_session_by_document_hash(
    db: AsyncSession, document_hash: str, owner_id: uuid.UUID
) -> Optional[Session]:
    """Find a non-archived session whose stored document has an identical
    content hash, so a fresh upload of an already-evaluated file nests into
    the existing session instead of creating a duplicate one."""
    result = await db.execute(
        select(Session)
        .join(Document, Document.session_id == Session.id)
        .where(
            Document.document_hash == document_hash,
            Session.owner_id == owner_id,
            Session.archived_at.is_(None),
        )
        .order_by(Session.created_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_session(
    db: AsyncSession,
    *,
    document_text: str,
    owner_id: uuid.UUID,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    content: Optional[bytes] = None,
    pages: Optional[list] = None,
) -> tuple[Session, EvaluationVersion]:
    """Create a new session, its immutable document record, and version 1."""
    clean_document_text = sanitize_for_postgres(document_text)
    clean_filename = sanitize_for_postgres(filename)
    clean_content_type = sanitize_for_postgres(content_type)
    clean_pages = sanitize_for_postgres(pages)

    session_row = Session(owner_id=owner_id, filename=clean_filename, content_type=clean_content_type)
    db.add(session_row)
    await db.flush()  # populate session_row.id

    db.add(
        Document(
            session_id=session_row.id,
            document_text=clean_document_text,
            content=content,
            content_type=clean_content_type,
            filename=clean_filename,
            pages=clean_pages,
            document_hash=hash_document(content, clean_document_text),
        )
    )

    version = EvaluationVersion(
        session_id=session_row.id,
        version_number=1,
        is_current=True,
        status="queued",
        stage="pending",
        progress=0,
    )
    db.add(version)
    await db.commit()
    await db.refresh(session_row)
    await db.refresh(version)
    return session_row, version


async def create_reevaluation(
    db: AsyncSession, session_id: uuid.UUID, owner_id: uuid.UUID
) -> EvaluationVersion:
    """Start a new version under an existing session, reusing its stored
    document. Raises LookupError if the session or its document is missing."""
    session_row = await db.scalar(
        select(Session).where(Session.id == session_id, Session.owner_id == owner_id)
    )
    if session_row is None or session_row.archived_at is not None:
        raise LookupError(f"Session '{session_id}' not found.")

    document = await db.get(Document, session_id)
    if document is None:
        raise LookupError(f"Session '{session_id}' has no stored document.")

    max_version = await db.scalar(
        select(func.max(EvaluationVersion.version_number)).where(
            EvaluationVersion.session_id == session_id
        )
    )
    next_number = (max_version or 0) + 1

    await db.execute(
        update(EvaluationVersion)
        .where(EvaluationVersion.session_id == session_id)
        .values(is_current=False)
    )

    version = EvaluationVersion(
        session_id=session_id,
        version_number=next_number,
        is_current=True,
        status="queued",
        stage="pending",
        progress=0,
    )
    db.add(version)
    session_row.updated_at = _utcnow()
    await db.commit()
    await db.refresh(version)
    return version


async def update_version(db: AsyncSession, version_id: uuid.UUID, **fields) -> None:
    if fields.get("status") == "running" or "progress" in fields:
        fields.setdefault("heartbeat_at", _utcnow())
    await db.execute(
        update(EvaluationVersion).where(EvaluationVersion.id == version_id).values(**fields)
    )
    await db.execute(
        update(Session)
        .where(
            Session.id
            == select(EvaluationVersion.session_id)
            .where(EvaluationVersion.id == version_id)
            .scalar_subquery()
        )
        .values(updated_at=_utcnow())
    )
    await db.commit()


async def set_version_result(
    db: AsyncSession, version_id: uuid.UUID, result: EvaluationResult
) -> None:
    scoring = result.scoring.model_dump() if result.scoring else {}
    await update_version(
        db,
        version_id,
        status="complete",
        stage="complete",
        progress=100,
        result_json=result.model_dump(),
        final_score=scoring.get("final_score"),
        grade_band=scoring.get("grade_band"),
        completed_at=_utcnow(),
        worker_id=None,
        claimed_at=None,
        heartbeat_at=None,
    )


async def set_version_failed(db: AsyncSession, version_id: uuid.UUID, error: str) -> None:
    await update_version(
        db,
        version_id,
        status="failed",
        stage="failed",
        error=error[:4000],
        worker_id=None,
        claimed_at=None,
        heartbeat_at=None,
        completed_at=_utcnow(),
    )


async def count_active_versions(db: AsyncSession, owner_id: uuid.UUID) -> int:
    # Serialize submissions for one account until the surrounding transaction
    # commits, so concurrent requests cannot race past the active-job limit.
    advisory_key = owner_id.int & 0x7FFF_FFFF_FFFF_FFFF
    await db.execute(select(func.pg_advisory_xact_lock(advisory_key)))
    count = await db.scalar(
        select(func.count(EvaluationVersion.id))
        .join(Session, Session.id == EvaluationVersion.session_id)
        .where(
            Session.owner_id == owner_id,
            EvaluationVersion.status.in_(("queued", "running")),
        )
    )
    return int(count or 0)


async def claim_next_queued_version(
    db: AsyncSession,
    *,
    worker_id: str,
    max_attempts: int,
) -> Optional[ClaimedEvaluation]:
    version = await db.scalar(
        select(EvaluationVersion)
        .where(
            EvaluationVersion.status == "queued",
            EvaluationVersion.attempt_count < max_attempts,
        )
        .order_by(EvaluationVersion.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if version is None:
        await db.rollback()
        return None

    document = await db.get(Document, version.session_id)
    if document is None:
        version.status = "failed"
        version.stage = "failed"
        version.error = "Stored document is missing."
        version.completed_at = _utcnow()
        await db.commit()
        return None

    now = _utcnow()
    version.status = "running"
    version.stage = "starting"
    version.completed_at = None
    version.error = None
    version.worker_id = worker_id
    version.claimed_at = now
    version.heartbeat_at = now
    version.attempt_count += 1
    await db.commit()

    return ClaimedEvaluation(
        version_id=version.id,
        document_text=document.document_text,
        pages=document.pages,
        attempt_count=version.attempt_count,
    )


async def retry_or_fail_version(
    db: AsyncSession,
    version_id: uuid.UUID,
    *,
    max_attempts: int,
    error: str,
) -> None:
    version = await db.get(EvaluationVersion, version_id, with_for_update=True)
    if version is None:
        await db.rollback()
        return

    version.worker_id = None
    version.claimed_at = None
    version.heartbeat_at = None
    version.error = error[:4000]
    if version.attempt_count < max_attempts:
        version.status = "queued"
        version.stage = "pending"
        version.progress = 0
        version.completed_at = None
    else:
        version.status = "failed"
        version.stage = "failed"
        version.completed_at = _utcnow()
    await db.commit()


async def recover_stale_versions(
    db: AsyncSession,
    *,
    stale_before: datetime,
    max_attempts: int,
) -> tuple[int, int]:
    stale_versions = (
        await db.scalars(
            select(EvaluationVersion)
            .where(
                EvaluationVersion.status == "running",
                or_(
                    EvaluationVersion.heartbeat_at.is_(None),
                    EvaluationVersion.heartbeat_at < stale_before,
                ),
            )
            .with_for_update(skip_locked=True)
        )
    ).all()

    requeued = 0
    failed = 0
    for version in stale_versions:
        version.worker_id = None
        version.claimed_at = None
        version.heartbeat_at = None
        if version.attempt_count < max_attempts:
            version.status = "queued"
            version.stage = "pending"
            version.progress = 0
            version.completed_at = None
            version.error = "Recovered after an interrupted worker run."
            requeued += 1
        else:
            version.status = "failed"
            version.stage = "failed"
            version.error = "Evaluation failed after repeated worker interruption."
            version.completed_at = _utcnow()
            failed += 1
    await db.commit()
    return requeued, failed


async def get_version(
    db: AsyncSession, version_id: uuid.UUID, owner_id: Optional[uuid.UUID] = None
) -> Optional[EvaluationVersion]:
    if owner_id is None:
        return await db.get(EvaluationVersion, version_id)
    return await db.scalar(
        select(EvaluationVersion)
        .join(Session, Session.id == EvaluationVersion.session_id)
        .where(EvaluationVersion.id == version_id, Session.owner_id == owner_id)
    )


async def get_session(
    db: AsyncSession, session_id: uuid.UUID, owner_id: Optional[uuid.UUID] = None
) -> Optional[Session]:
    query = (
        select(Session)
        .options(selectinload(Session.versions))
        .where(Session.id == session_id)
    )
    if owner_id is not None:
        query = query.where(Session.owner_id == owner_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_document(db: AsyncSession, session_id: uuid.UUID) -> Optional[Document]:
    return await db.get(Document, session_id)


async def get_document_for_version(
    db: AsyncSession, version_id: uuid.UUID, owner_id: Optional[uuid.UUID] = None
) -> Optional[Document]:
    version = await get_version(db, version_id, owner_id)
    if version is None:
        return None
    return await get_document(db, version.session_id)


async def list_sessions(
    db: AsyncSession,
    *,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
    owner_id: Optional[uuid.UUID] = None,
) -> Sequence[Session]:
    query = select(Session).options(selectinload(Session.versions)).order_by(Session.updated_at.desc())
    if not include_archived:
        query = query.where(Session.archived_at.is_(None))
    if owner_id is not None:
        query = query.where(Session.owner_id == owner_id)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


async def archive_session(db: AsyncSession, session_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
    session_row = await db.scalar(
        select(Session).where(Session.id == session_id, Session.owner_id == owner_id)
    )
    if session_row is None:
        return False
    session_row.archived_at = _utcnow()
    await db.commit()
    return True


async def unarchive_session(db: AsyncSession, session_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
    session_row = await db.scalar(
        select(Session).where(Session.id == session_id, Session.owner_id == owner_id)
    )
    if session_row is None:
        return False
    session_row.archived_at = None
    await db.commit()
    return True
