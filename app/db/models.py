import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, LargeBinary, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """An application account authenticated by password, Google, or both."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    # Passwords are never stored.  This field contains a versioned, salted
    # scrypt hash and is nullable for Google-only accounts.
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    google_subject: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[List["Session"]] = relationship(back_populates="owner")


class Session(Base):
    """A logical evaluation session — one submitted document, grouping every
    version (original run + every re-evaluation) ever produced for it.
    Rows are never hard-deleted; `archived_at` hides a session from the
    default list without destroying its history."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    versions: Mapped[List["EvaluationVersion"]] = relationship(
        back_populates="session",
        order_by="EvaluationVersion.version_number",
        cascade="all, delete-orphan",
    )
    document: Mapped[Optional["Document"]] = relationship(
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    owner: Mapped[Optional["User"]] = relationship(back_populates="sessions")


class EvaluationVersion(Base):
    """One pipeline run for a session. The original evaluation is version 1;
    every re-evaluation appends a new row rather than overwriting the last —
    this is the durable history the sessions drawer reads from. `id` is the
    externally-visible `job_id` used by the existing status/result endpoints."""

    __tablename__ = "evaluation_versions"
    __table_args__ = (
        UniqueConstraint("session_id", "version_number", name="uq_session_version"),
        Index("ix_evaluation_versions_queue", "status", "created_at"),
        Index("ix_evaluation_versions_heartbeat", "status", "heartbeat_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False)

    status: Mapped[str] = mapped_column(String, default="queued", nullable=False)
    stage: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    worker_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    result_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    final_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade_band: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["Session"] = relationship(back_populates="versions")


class Document(Base):
    """The submission input for a session (immutable once created). Shared by
    every version so re-evaluating never needs the original upload to still
    be present client-side — it re-runs the pipeline against what's stored here."""

    __tablename__ = "documents"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True
    )
    document_text: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pages: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    session: Mapped["Session"] = relationship(back_populates="document")
