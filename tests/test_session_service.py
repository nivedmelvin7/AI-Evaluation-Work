"""Tests for normalising document data before PostgreSQL persistence."""

import asyncio
import hashlib
import uuid

from app.db.models import Document, Session
from app.services.session_service import create_session, hash_document, sanitize_for_postgres


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
