"""
Stage 5: Self-Critique Audit

Input:  llm (LLMService), reviewer_name (str), reviewer_out (Dict from stage 2/3/4)
Output: Dict with keys:
          reviewer_name  (str)
          raw_xml        (str)
          issues         (List[Dict])
          overall_quality (str)
          audit_summary  (str)

Temperature: 0.0 (deterministic)
Self-consistency: No
"""

import sys
from typing import Dict, Any

from app.services.llm_service import LLMService
from app.prompts.templates import SELF_CRITIQUE_SYSTEM, SELF_CRITIQUE_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response


async def run(
    llm: LLMService,
    reviewer_name: str,
    reviewer_out: Dict[str, Any],
) -> Dict[str, Any]:
    """Audit reviewer output for quality issues."""
    raw_xml = reviewer_out.get("raw_xml", "")
    if not raw_xml:
        # Fallback: format scores as text if no raw XML captured
        scores = reviewer_out.get("scores", {})
        raw_xml = "\n".join(
            f"{crit}: score={data.get('score', '?')}, confidence={data.get('confidence', '?')}"
            for crit, data in scores.items()
        )

    user_prompt = SELF_CRITIQUE_USER_TEMPLATE.format(
        reviewer_name=reviewer_name,
        reviewer_output=raw_xml,
    )

    try:
        raw = await llm.complete_with_retry(
            system_prompt=SELF_CRITIQUE_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception as e:
        print(f"[Stage 5] LLM call failed for {reviewer_name}: {e}", file=sys.stderr)
        return _empty_audit(reviewer_name)

    parsed = parse_xml_response(raw, "audit")

    issues = []
    overall_quality = "Medium"
    audit_summary = ""

    if parsed is not None:
        for issue_el in parsed.findall(".//issue"):
            type_el = issue_el.find("type")
            criterion_el = issue_el.find("criterion_affected")
            desc_el = issue_el.find("description")
            rec_el = issue_el.find("recommended_correction")
            issues.append({
                "type": type_el.text.strip() if type_el is not None and type_el.text else "NONE",
                "criterion_affected": criterion_el.text.strip() if criterion_el is not None and criterion_el.text else "",
                "description": desc_el.text.strip() if desc_el is not None and desc_el.text else "",
                "recommended_correction": rec_el.text.strip() if rec_el is not None and rec_el.text else "",
            })

        oq_el = parsed.find("overall_quality")
        if oq_el is not None and oq_el.text:
            overall_quality = oq_el.text.strip()

        summary_el = parsed.find("audit_summary")
        if summary_el is not None and summary_el.text:
            audit_summary = summary_el.text.strip()
    else:
        print(f"[Stage 5] XML parse failed for {reviewer_name} audit.", file=sys.stderr)

    return {
        "reviewer_name": reviewer_name,
        "raw_xml": raw,
        "issues": issues,
        "overall_quality": overall_quality,
        "audit_summary": audit_summary,
    }


def _empty_audit(reviewer_name: str) -> Dict[str, Any]:
    return {
        "reviewer_name": reviewer_name,
        "raw_xml": "",
        "issues": [],
        "overall_quality": "Low",
        "audit_summary": "Audit failed due to LLM error.",
    }
