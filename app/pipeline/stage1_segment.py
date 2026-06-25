"""
Stage 1: Document Segmentation

Input:  llm (LLMService), document_text (str)
Output: List[Dict] — each dict has section_name, section_type,
        content, word_count, status

Temperature: 0.0 (deterministic)
Self-consistency: No
"""

import json
import logging
import re
import time
from typing import Any, Dict, List

from app.services.llm_service import LLMService
from app.prompts.templates import SEGMENTATION_SYSTEM, SEGMENTATION_USER_TEMPLATE

logger = logging.getLogger(__name__)


async def run(llm: LLMService, document_text: str) -> List[Dict[str, Any]]:
    """Segment the document into labelled sections via LLM JSON output."""
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

    # Strip markdown fences
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()

    # Extract the JSON array
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start: end + 1]
    else:
        logger.warning("Stage 1 — could not find JSON array brackets in LLM response; using fallback")
        return _fallback_section(document_text)

    try:
        sections = json.loads(raw)
        if not isinstance(sections, list) or len(sections) == 0:
            raise ValueError("Empty or non-list response")
        validated = []
        for s in sections:
            validated.append({
                "section_name": s.get("section_name", "Unknown"),
                "section_type": s.get("section_type", "OTHER"),
                "content": s.get("content", ""),
                "word_count": s.get("word_count", len(s.get("content", "").split())),
                "status": s.get("status", "PRESENT"),
            })
        logger.info("Stage 1 — parsed %d sections successfully", len(validated))
        return validated
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Stage 1 — JSON parse failed (%s); using fallback single-section", exc)
        return _fallback_section(document_text)


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
