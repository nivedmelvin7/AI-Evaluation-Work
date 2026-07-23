"""
Stage 6: Reflection Pass

Input:  llm (LLMService), reviewer_name (str),
        original_out (Dict from stage 2/3/4),
        audit_out    (Dict from stage 5),
        sections     (List[Dict] from stage 1)
Output: Dict with keys:
          reviewer_name  (str)
          raw_xml        (str)
          final_scores   (Dict) — {criterion: {score, confidence}}

Temperature: 0.0 (deterministic)
Self-consistency: No
"""

import logging
import re
import time
from typing import Any, Dict, List

from app.services.llm_service import LLMService
from app.prompts.stage6_reflection_prompts import REFLECTION_SYSTEM, REFLECTION_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response
from app.pipeline import format_sections_for_prompt

logger = logging.getLogger(__name__)


async def run(
    llm: LLMService,
    reviewer_name: str,
    original_out: Dict[str, Any],
    audit_out: Dict[str, Any],
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Reviewer revisits evaluation in light of audit feedback."""
    logger.info("Stage 6 (reflection) — processing %r", reviewer_name)

    doc_sections_text = format_sections_for_prompt(sections)
    original_xml = original_out.get("raw_xml", "")
    if not original_xml:
        original_xml = str(original_out.get("scores", {}))
        logger.debug("Stage 6 (%s) — no raw XML; using stringified scores", reviewer_name)

    audit_xml = audit_out.get("raw_xml", "")
    if not audit_xml:
        audit_xml = str(audit_out.get("issues", []))
        logger.debug("Stage 6 (%s) — no audit XML; using stringified issues", reviewer_name)

    n_issues = len(audit_out.get("issues", []))
    logger.debug(
        "Stage 6 (%s) — audit had %d issue(s), quality=%s",
        reviewer_name, n_issues, audit_out.get("overall_quality"),
    )

    user_prompt = REFLECTION_USER_TEMPLATE.format(
        reviewer_name=reviewer_name,
        original_output=original_xml,
        audit_output=audit_xml,
        document_sections=doc_sections_text,
    )

    t0 = time.perf_counter()
    try:
        raw = await llm.complete_with_retry(
            system_prompt=REFLECTION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception:
        logger.exception("Stage 6 — LLM call failed for %r; falling back to original scores", reviewer_name)
        return _fallback_result(reviewer_name, original_out)

    logger.debug("Stage 6 (%s) — LLM response received (%.2fs, %d chars)", reviewer_name, time.perf_counter() - t0, len(raw))

    final_scores = _parse_final_scores(raw)

    if not final_scores:
        logger.warning(
            "Stage 6 (%s) — could not parse final_scores; falling back to original scores",
            reviewer_name,
        )
        final_scores = {
            crit: {"score": data["score"], "confidence": data["confidence"]}
            for crit, data in original_out.get("scores", {}).items()
        }
    else:
        logger.info(
            "Stage 6 (%s) complete — final scores=%s",
            reviewer_name,
            {k: v.get("score") for k, v in final_scores.items()},
        )

    return {
        "reviewer_name": reviewer_name,
        "raw_xml": raw,
        "final_scores": final_scores,
    }


def _parse_final_scores(raw: str) -> Dict[str, Dict[str, Any]]:
    """Extract criterion scores from <final_scores> block."""
    parsed = parse_xml_response(raw, "final_scores")
    if parsed is None:
        return {}

    final_scores: Dict[str, Dict[str, Any]] = {}
    for score_el in parsed.findall(".//score"):
        criterion = score_el.get("criterion", "").strip()
        value_str = score_el.get("value", "2").strip()
        confidence = score_el.get("confidence", "medium").strip().lower()

        if value_str.lower().startswith("unchanged"):
            match = re.search(r"\d", value_str)
            val = int(match.group()) if match else 2
        else:
            try:
                val = int(value_str)
            except ValueError:
                val = 2

        if criterion:
            final_scores[criterion] = {
                "score": max(0, min(4, val)),
                "confidence": confidence,
            }

    return final_scores


def _fallback_result(
    reviewer_name: str, original_out: Dict[str, Any]
) -> Dict[str, Any]:
    fallback_scores = {
        crit: {"score": data["score"], "confidence": data["confidence"]}
        for crit, data in original_out.get("scores", {}).items()
    }
    return {
        "reviewer_name": reviewer_name,
        "raw_xml": "",
        "final_scores": fallback_scores,
    }
