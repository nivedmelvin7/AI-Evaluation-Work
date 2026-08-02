"""Stage 6: require complete structured reflection assessments."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Tuple

from app.pipeline import format_sections_for_prompt, sections_as_document_text
from app.prompts.stage6_reflection_prompts import REFLECTION_SYSTEM, REFLECTION_USER_TEMPLATE
from app.services.llm_service import LLMService
from app.utils.xml_parser import parse_review_assessments, parse_xml_response

logger = logging.getLogger(__name__)


async def run(
    llm: LLMService,
    reviewer_name: str,
    original_out: Dict[str, Any],
    audit_out: Dict[str, Any],
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Reflect only when both the source assessment and audit are complete.

    A failed audit/reflection carries forward the last complete reviewer
    assessment as a *provisional* record and declares an integrity failure.
    """
    original_scores = original_out.get("scores", {})
    expected = tuple(original_scores)
    if not original_out.get("complete") or not expected:
        return _provisional(reviewer_name, original_scores, "reviewer assessment incomplete")
    if not audit_out.get("complete"):
        return _provisional(
            reviewer_name, original_scores,
            "audit failed validation: " + "; ".join(audit_out.get("validation_errors", [])),
        )

    user_prompt = REFLECTION_USER_TEMPLATE.format(
        reviewer_name=reviewer_name,
        original_output=json.dumps(original_scores, indent=2, ensure_ascii=False),
        audit_output=json.dumps(audit_out.get("issues", []), indent=2, ensure_ascii=False),
        document_sections=format_sections_for_prompt(sections),
    )
    try:
        raw = await llm.complete_with_retry(
            system_prompt=REFLECTION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception as exc:
        return _provisional(reviewer_name, original_scores, f"reflection LLM request failed: {exc.__class__.__name__}")

    parsed = parse_xml_response(raw, "final_scores")
    if parsed is None:
        return _provisional(reviewer_name, original_scores, "reflection response was not valid final_scores XML", raw)
    final_scores, errors = parse_review_assessments(
        parsed,
        expected,
        sections_as_document_text(sections),
        reviewer_name,
        1,
    )
    if errors:
        return _provisional(reviewer_name, original_scores, "; ".join(errors), raw)
    return {
        "reviewer_name": reviewer_name,
        "raw_xml": raw,
        "final_scores": final_scores,
        "complete": True,
        "integrity_flags": [],
        "validation_errors": [],
        "provisional": False,
    }


def _provisional(
    reviewer_name: str, scores: Dict[str, Any], reason: str, raw_xml: str = ""
) -> Dict[str, Any]:
    logger.warning("Stage 6 reflection provisional for %s: %s", reviewer_name, reason)
    return {
        "reviewer_name": reviewer_name,
        "raw_xml": raw_xml,
        "final_scores": {criterion: dict(score) for criterion, score in scores.items()},
        "complete": False,
        "integrity_flags": ["provisional_after_audit_or_reflection_failure"],
        "validation_errors": [reason],
        "provisional": True,
    }
