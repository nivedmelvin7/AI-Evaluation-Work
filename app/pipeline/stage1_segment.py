"""
Stage 1: Document Segmentation

Input:  llm (LLMService), document_text (str)
Output: List[Dict] — each dict has section_name, section_type,
        content, word_count, status

Temperature: 0.0 (deterministic)
Self-consistency: No
"""

import json
import re
import sys
from typing import List, Dict, Any

from app.services.llm_service import LLMService
from app.prompts.templates import SEGMENTATION_SYSTEM, SEGMENTATION_USER_TEMPLATE


async def run(llm: LLMService, document_text: str) -> List[Dict[str, Any]]:
    """Segment the document into labelled sections via LLM JSON output."""
    user_prompt = SEGMENTATION_USER_TEMPLATE.format(document_text=document_text)

    try:
        raw = await llm.complete_with_retry(
            system_prompt=SEGMENTATION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception as e:
        print(f"[Stage 1] LLM call failed: {e}", file=sys.stderr)
        return _fallback_section(document_text)

    # Strip markdown fences
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()

    # Extract the JSON array
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start: end + 1]

    try:
        sections = json.loads(raw)
        if not isinstance(sections, list) or len(sections) == 0:
            raise ValueError("Empty or non-list response")
        # Validate required keys; fill defaults where missing
        validated = []
        for s in sections:
            validated.append({
                "section_name": s.get("section_name", "Unknown"),
                "section_type": s.get("section_type", "OTHER"),
                "content": s.get("content", ""),
                "word_count": s.get("word_count", len(s.get("content", "").split())),
                "status": s.get("status", "PRESENT"),
            })
        return validated
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[Stage 1] JSON parse failed: {e}", file=sys.stderr)
        return _fallback_section(document_text)


def _fallback_section(document_text: str) -> List[Dict[str, Any]]:
    """Return the entire document as one section when segmentation fails."""
    return [{
        "section_name": "Full Document",
        "section_type": "OTHER",
        "content": document_text,
        "word_count": len(document_text.split()),
        "status": "PRESENT",
    }]
