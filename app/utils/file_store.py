"""In-memory store for original uploaded file bytes, keyed by job_id."""
from typing import Dict, List, Optional, Tuple


class FileStore:

    def __init__(self):
        self._store: Dict[str, dict] = {}

    def save(
        self,
        job_id: str,
        content: bytes,
        content_type: str,
        filename: str,
        pages: Optional[List[dict]] = None,
    ) -> None:
        self._store[job_id] = {
            "content": content,
            "content_type": content_type,
            "filename": filename,
            "pages": pages or [],
        }

    def get_meta(self, job_id: str) -> Optional[dict]:
        entry = self._store.get(job_id)
        if not entry:
            return None
        ct = entry["content_type"]
        if "pdf" in ct:
            file_type = "pdf"
        elif "openxmlformats" in ct or "msword" in ct or "docx" in ct or "doc" in ct:
            file_type = "docx"
        else:
            file_type = "txt"
        return {
            "type": file_type,
            "filename": entry["filename"],
            "num_pages": len(entry["pages"]),
        }

    def get_content(self, job_id: str) -> Optional[Tuple[bytes, str]]:
        entry = self._store.get(job_id)
        if not entry:
            return None
        return entry["content"], entry["content_type"]

    def get_pages(self, job_id: str) -> Optional[List[dict]]:
        entry = self._store.get(job_id)
        if not entry:
            return None
        return entry["pages"]

    def delete(self, job_id: str) -> None:
        self._store.pop(job_id, None)


file_store = FileStore()
