"""
Document parsing service.
Supports: .pdf (PyMuPDF), .docx (python-docx), .txt (plain text)
Returns plain text string.
"""

import io
from pathlib import Path

import fitz  # PyMuPDF
import docx


class DocumentService:

    def parse_file(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return self._parse_pdf(content)
        elif ext in (".docx", ".doc"):
            return self._parse_docx(content)
        elif ext == ".txt":
            return content.decode("utf-8", errors="replace")
        else:
            raise ValueError(
                f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT."
            )

    def _parse_pdf(self, content: bytes) -> str:
        doc = fitz.open(stream=content, filetype="pdf")
        pages = [page.get_text() for page in doc]
        return "\n\n".join(pages)

    def _parse_docx(self, content: bytes) -> str:
        doc = docx.Document(io.BytesIO(content))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
