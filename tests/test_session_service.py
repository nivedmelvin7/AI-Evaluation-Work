"""Tests for normalising document data before PostgreSQL persistence."""

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone

from app.db.models import Document, EvaluationVersion, Session
from app.services.session_service import (
    claim_next_queued_version,
    create_session,
    hash_document,
    recover_stale_versions,
    retry_or_fail_version,
    sanitize_for_postgres,
)


def test_sanitize_for_postgres_removes_nul_from_nested_json_values_and_keys():
    raw = {"pa\x00ge": [{"text": "First\x00 page"}, {"nested": ["A\x00B", 2]}]}

    assert sanitize_for_postgres(raw) == {
        "page": [{"text": "First page"}, {"nested": ["AB", 2]}]
    }


def test_text_hash_uses_the_same_normalised_text_as_persistence():
    assert hash_document(None, "A\x00B") == hash_document(None, "AB")
    assert hash_document(b"A\x00B", "unrelated") == hashlib.sha256(b"A\x00B").hexdigest()


def test_create_session_sanitizes_text_and_pages_but_retains_binary_upload():
    class FakeSession:
        def __init__(self):
            self.added = []

        def add(self, value):
            self.added.append(value)

        async def flush(self):
            next(value for value in self.added if isinstance(value, Session)).id = uuid.uuid4()

        async def commit(self):
            pass

        async def refresh(self, _value):
            pass

    db = FakeSession()
    original_content = b"%PDF\x00binary-content"

    asyncio.run(
        create_session(
            db,
            document_text="Extracted\x00 text",
            owner_id=uuid.uuid4(),
            filename="report\x00.pdf",
            content_type="application/pdf",
            content=original_content,
            pages=[{"page": 1, "text": "Page\x00 one"}],
        )
    )

    document = next(value for value in db.added if isinstance(value, Document))
    assert document.document_text == "Extracted text"
    assert document.filename == "report.pdf"
    assert document.pages == [{"page": 1, "text": "Page one"}]
    assert document.content == original_content


def test_claim_and_retry_job_state_transitions():
    version = EvaluationVersion(
        session_id=uuid.uuid4(),
        version_number=1,
        status="queued",
        stage="pending",
        progress=0,
        attempt_count=0,
    )
    version.id = uuid.uuid4()
    document = Document(
        session_id=version.session_id,
        document_text="Stored report",
        pages=[{"page": 1, "text": "Stored report"}],
    )

    class FakeQueueSession:
        async def scalar(self, _query):
            return version

        async def get(self, model, _key, **_kwargs):
            return document if model is Document else version

        async def commit(self):
            pass

        async def rollback(self):
            pass

    db = FakeQueueSession()
    claimed = asyncio.run(
        claim_next_queued_version(db, worker_id="worker-1", max_attempts=2)
    )

    assert claimed.version_id == version.id
    assert claimed.document_text == "Stored report"
    assert claimed.attempt_count == 1
    assert version.status == "running"
    assert version.worker_id == "worker-1"
    assert version.heartbeat_at is not None

    asyncio.run(
        retry_or_fail_version(db, version.id, max_attempts=2, error="temporary failure")
    )
    assert version.status == "queued"
    assert version.stage == "pending"
    assert version.worker_id is None

    version.attempt_count = 2
    asyncio.run(
        retry_or_fail_version(db, version.id, max_attempts=2, error="final failure")
    )
    assert version.status == "failed"
    assert version.completed_at is not None


def test_stale_jobs_are_requeued_or_failed_by_attempt_count():
    retryable = EvaluationVersion(
        session_id=uuid.uuid4(),
        version_number=1,
        status="running",
        stage="reviewing",
        progress=40,
        attempt_count=1,
        worker_id="lost-worker",
    )
    exhausted = EvaluationVersion(
        session_id=uuid.uuid4(),
        version_number=1,
        status="running",
        stage="reviewing",
        progress=40,
        attempt_count=2,
        worker_id="lost-worker",
    )

    class ScalarRows:
        def all(self):
            return [retryable, exhausted]

    class FakeRecoverySession:
        async def scalars(self, _query):
            return ScalarRows()

        async def commit(self):
            pass

    requeued, failed = asyncio.run(
        recover_stale_versions(
            FakeRecoverySession(),
            stale_before=datetime.now(timezone.utc),
            max_attempts=2,
        )
    )

    assert (requeued, failed) == (1, 1)
    assert retryable.status == "queued"
    assert retryable.progress == 0
    assert exhausted.status == "failed"
    assert exhausted.completed_at is not None
