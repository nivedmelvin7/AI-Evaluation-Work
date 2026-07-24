"""
Durable session/version persistence — replaces the old in-memory job_store
and file_store. A "session" is one submitted document; each pipeline run
against it (the original evaluation and every re-evaluation) is stored as
its own EvaluationVersion row. Versions are never deleted, so past analyses
always remain retrievable even after a re-evaluation produces a new one.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Document, EvaluationVersion, Session
from app.models.response_models import EvaluationResult


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def create_session(
    db: AsyncSession,
    *,
    document_text: str,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    content: Optional[bytes] = None,
    pages: Optional[list] = None,
) -> tuple[Session, EvaluationVersion]:
    """Create a new session, its immutable document record, and version 1."""
    session_row = Session(filename=filename, content_type=content_type)
    db.add(session_row)
    await db.flush()  # populate session_row.id

    db.add(
        Document(
            session_id=session_row.id,
            document_text=document_text,
            content=content,
            content_type=content_type,
            filename=filename,
            pages=pages,
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


async def create_reevaluation(db: AsyncSession, session_id: uuid.UUID) -> EvaluationVersion:
    """Start a new version under an existing session, reusing its stored
    document. Raises LookupError if the session or its document is missing."""
    session_row = await db.get(Session, session_id)
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
    scoring = result.scoring or {}
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
    )


async def set_version_failed(db: AsyncSession, version_id: uuid.UUID, error: str) -> None:
    await update_version(db, version_id, status="failed", error=error)


async def get_version(db: AsyncSession, version_id: uuid.UUID) -> Optional[EvaluationVersion]:
    return await db.get(EvaluationVersion, version_id)


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Optional[Session]:
    result = await db.execute(
        select(Session)
        .options(selectinload(Session.versions))
        .where(Session.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_document(db: AsyncSession, session_id: uuid.UUID) -> Optional[Document]:
    return await db.get(Document, session_id)


async def get_document_for_version(
    db: AsyncSession, version_id: uuid.UUID
) -> Optional[Document]:
    version = await get_version(db, version_id)
    if version is None:
        return None
    return await get_document(db, version.session_id)


async def list_sessions(
    db: AsyncSession,
    *,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Session]:
    query = select(Session).options(selectinload(Session.versions)).order_by(Session.updated_at.desc())
    if not include_archived:
        query = query.where(Session.archived_at.is_(None))
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


async def archive_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
    session_row = await db.get(Session, session_id)
    if session_row is None:
        return False
    session_row.archived_at = _utcnow()
    await db.commit()
    return True


async def unarchive_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
    session_row = await db.get(Session, session_id)
    if session_row is None:
        return False
    session_row.archived_at = None
    await db.commit()
    return True
