"""
Stage 1: Document Segmentation

Input:  llm (LLMService), document_text (str)
Output: List[Dict] — each dict has section_name, section_type,
        content, word_count, status

The LLM returns only SECTION BOUNDARIES (short verbatim anchor snippets),
not the full text of each section. This stage reconstructs each section's
content by locating those anchors in the original document. Reproducing whole
sections verbatim inside a JSON string is what previously truncated/malformed
the response; emitting a few short snippets is far more reliable.

Temperature: 0.0 (deterministic)
Self-consistency: No
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from app.services.llm_service import LLMService
from app.prompts.stage1_segmentation_prompts import SEGMENTATION_SYSTEM, SEGMENTATION_USER_TEMPLATE

logger = logging.getLogger(__name__)


async def run(llm: LLMService, document_text: str) -> List[Dict[str, Any]]:
    """Segment the document into labelled sections via LLM boundary markers."""
    logger.info("Stage 1 — segmenting document (%d chars)", len(document_text))
    user_prompt = SEGMENTATION_USER_TEMPLATE.format(document_text=document_text)

    t0 = time.perf_counter()
    try:
        raw = await llm.complete_with_retry(
            system_prompt=SEGMENTATION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception:
        logger.exception("Stage 1 — LLM call failed; using fallback single-section")
        return _fallback_section(document_text)

    logger.debug("Stage 1 — LLM response received (%.2fs, %d chars)", time.perf_counter() - t0, len(raw))

    markers = _parse_markers(raw)
    if not markers:
        logger.warning("Stage 1 — could not parse boundary markers; using fallback single-section")
        return _fallback_section(document_text)

    sections = _reconstruct_sections(markers, document_text)
    if not any(s["status"] == "PRESENT" and s["content"].strip() for s in sections):
        logger.warning("Stage 1 — no section content could be reconstructed from markers; using fallback")
        return _fallback_section(document_text)

    present = sum(1 for s in sections if s["status"] == "PRESENT")
    logger.info("Stage 1 — reconstructed %d sections (%d present)", len(sections), present)
    return sections


def _parse_markers(raw: str) -> List[Dict[str, Any]]:
    """Extract the JSON array of section boundary markers from the LLM output."""
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()

    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1:
        return []
    raw = raw[start: end + 1]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Stage 1 — marker JSON parse failed (%s)", exc)
        return []
    if not isinstance(data, list):
        return []
    return [m for m in data if isinstance(m, dict)]


def _normalise_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _find_snippet(document: str, snippet: str, from_idx: int) -> int:
    """
    Locate a verbatim snippet in the document at or after from_idx.
    Falls back to a whitespace-insensitive search when the exact copy differs
    only in run-of-whitespace (line wraps, double spaces).
    Returns the character index of the match start, or -1.
    """
    snippet = (snippet or "").strip()
    if not snippet:
        return -1

    idx = document.find(snippet, from_idx)
    if idx != -1:
        return idx

    # Whitespace-insensitive fallback: match the snippet's tokens allowing any
    # whitespace between them.
    tokens = _normalise_ws(snippet).split(" ")
    if not tokens:
        return -1
    pattern = r"\s+".join(re.escape(tok) for tok in tokens)
    m = re.search(pattern, document[from_idx:])
    return from_idx + m.start() if m else -1


def _reconstruct_sections(
    markers: List[Dict[str, Any]], document: str
) -> List[Dict[str, Any]]:
    """Turn boundary markers into full sections by slicing the original text."""
    # Pass 1: locate each present section's start, scanning forward so repeated
    # phrasing doesn't collapse two sections onto the same anchor.
    starts: List[Optional[int]] = []
    cursor = 0
    for m in markers:
        if str(m.get("status", "PRESENT")).upper() == "MISSING":
            starts.append(None)
            continue
        idx = _find_snippet(document, m.get("start_snippet", ""), cursor)
        starts.append(idx if idx != -1 else None)
        if idx != -1:
            cursor = idx + 1

    # Next located start (used as a hard stop when an end_snippet can't be found).
    def next_start_after(i: int) -> int:
        for j in range(i + 1, len(markers)):
            if starts[j] is not None:
                return starts[j]  # type: ignore[return-value]
        return len(document)

    sections: List[Dict[str, Any]] = []
    for i, m in enumerate(markers):
        name = m.get("section_name", "Unknown") or "Unknown"
        stype = m.get("section_type", "OTHER") or "OTHER"
        status = str(m.get("status", "PRESENT")).upper()

        if status == "MISSING" or starts[i] is None:
            sections.append({
                "section_name": name,
                "section_type": stype,
                "content": "",
                "word_count": 0,
                "status": "MISSING" if status == "MISSING" else "PRESENT",
            })
            continue

        s_idx = starts[i]
        boundary = next_start_after(i)
        end_snippet = (m.get("end_snippet", "") or "").strip()
        e_idx = _find_snippet(document, end_snippet, s_idx) if end_snippet else -1
        if e_idx != -1 and e_idx < boundary:
            content_end = min(e_idx + len(end_snippet), boundary)
        else:
            content_end = boundary

        content = document[s_idx:content_end].strip()
        sections.append({
            "section_name": name,
            "section_type": stype,
            "content": content,
            "word_count": len(content.split()),
            "status": "PRESENT",
        })

    return sections


def _fallback_section(document_text: str) -> List[Dict[str, Any]]:
    """Return the entire document as one section when segmentation fails."""
    logger.warning("Stage 1 — returning fallback single-section (%d words)", len(document_text.split()))
    return [{
        "section_name": "Full Document",
        "section_type": "OTHER",
        "content": document_text,
        "word_count": len(document_text.split()),
        "status": "PRESENT",
    }]
