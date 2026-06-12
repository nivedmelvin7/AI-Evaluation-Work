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

import re
import sys
from typing import Dict, Any, List

from app.services.llm_service import LLMService
from app.prompts.templates import REFLECTION_SYSTEM, REFLECTION_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response
from app.pipeline import format_sections_for_prompt


async def run(
    llm: LLMService,
    reviewer_name: str,
    original_out: Dict[str, Any],
    audit_out: Dict[str, Any],
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Reviewer revisits evaluation in light of audit feedback."""
    doc_sections_text = format_sections_for_prompt(sections)
    original_xml = original_out.get("raw_xml", "")
    if not original_xml:
        original_xml = str(original_out.get("scores", {}))

    audit_xml = audit_out.get("raw_xml", "")
    if not audit_xml:
        audit_xml = str(audit_out.get("issues", []))

    user_prompt = REFLECTION_USER_TEMPLATE.format(
        reviewer_name=reviewer_name,
        original_output=original_xml,
        audit_output=audit_xml,
        document_sections=doc_sections_text,
    )

    try:
        raw = await llm.complete_with_retry(
            system_prompt=REFLECTION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception as e:
        print(f"[Stage 6] LLM call failed for {reviewer_name}: {e}", file=sys.stderr)
        return _fallback_result(reviewer_name, original_out)

    # The response contains two root elements: <reflection> and <final_scores>.
    # Parse <final_scores> for the definitive per-criterion scores.
    final_scores = _parse_final_scores(raw)

    if not final_scores:
        print(
            f"[Stage 6] Could not parse final_scores for {reviewer_name} — "
            "falling back to original scores.",
            file=sys.stderr,
        )
        final_scores = {
            crit: {"score": data["score"], "confidence": data["confidence"]}
            for crit, data in original_out.get("scores", {}).items()
        }

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

        # Handle "Unchanged: 3" format
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
