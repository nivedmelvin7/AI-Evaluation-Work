"""Stage 5: audit the structured median assessment, not a raw last response."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.prompts.stage5_self_critique_prompts import SELF_CRITIQUE_SYSTEM, SELF_CRITIQUE_USER_TEMPLATE
from app.services.llm_service import LLMService
from app.utils.xml_parser import parse_xml_response

logger = logging.getLogger(__name__)


def _validate_audit(parsed: Any, expected_criteria: set[str]) -> tuple[List[Dict[str, str]], List[str], str, str]:
    errors: List[str] = []
    issues: List[Dict[str, str]] = []
    covered: set[str] = set()
    for issue_el in parsed.findall(".//issue"):
        issue = {
            "type": "".join((issue_el.findtext("type") or "").split()).upper(),
            "criterion_affected": (issue_el.findtext("criterion_affected") or "").strip(),
            "description": (issue_el.findtext("description") or "").strip(),
            "recommended_correction": (issue_el.findtext("recommended_correction") or "").strip(),
        }
        if not all(issue.values()):
            errors.append("audit issue is missing a required field")
            continue
        if issue["criterion_affected"] not in expected_criteria:
            errors.append(f"audit references unexpected criterion: {issue['criterion_affected']}")
            continue
        covered.add(issue["criterion_affected"])
        issues.append(issue)
    missing = expected_criteria - covered
    if missing:
        errors.extend(f"audit missing criterion: {criterion}" for criterion in sorted(missing))
    overall_quality = (parsed.findtext("overall_quality") or "").strip().lower()
    audit_summary = (parsed.findtext("audit_summary") or "").strip()
    if overall_quality not in {"high", "medium", "low"}:
        errors.append("audit overall_quality must be High, Medium, or Low")
    if not audit_summary:
        errors.append("audit_summary is required")
    return issues, errors, overall_quality, audit_summary


async def run(llm: LLMService, reviewer_name: str, reviewer_out: Dict[str, Any]) -> Dict[str, Any]:
    """Audit the authoritative median assessments and flag invalid audits."""
    expected_criteria = set(reviewer_out.get("scores", {}))
    if not reviewer_out.get("complete") or not expected_criteria:
        return {
            "reviewer_name": reviewer_name,
            "raw_xml": "",
            "issues": [],
            "overall_quality": "low",
            "audit_summary": "Audit skipped because reviewer assessment was incomplete.",
            "complete": False,
            "integrity_flags": ["reviewer_output_incomplete"],
            "validation_errors": list(reviewer_out.get("validation_errors", ["reviewer output incomplete"])),
        }

    structured_assessment = json.dumps(reviewer_out["scores"], indent=2, ensure_ascii=False)
    user_prompt = SELF_CRITIQUE_USER_TEMPLATE.format(
        reviewer_name=reviewer_name,
        reviewer_output=structured_assessment,
    )
    try:
        raw = await llm.complete_with_retry(
            system_prompt=SELF_CRITIQUE_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception as exc:
        return _failed_audit(reviewer_name, f"audit LLM request failed: {exc.__class__.__name__}")

    parsed = parse_xml_response(raw, "audit")
    if parsed is None:
        return _failed_audit(reviewer_name, "audit response was not valid XML", raw)
    issues, errors, overall_quality, audit_summary = _validate_audit(parsed, expected_criteria)
    if errors:
        return _failed_audit(reviewer_name, "; ".join(errors), raw)
    return {
        "reviewer_name": reviewer_name,
        "raw_xml": raw,
        "issues": issues,
        "overall_quality": overall_quality,
        "audit_summary": audit_summary,
        "complete": True,
        "integrity_flags": [],
        "validation_errors": [],
    }


def _failed_audit(reviewer_name: str, reason: str, raw_xml: str = "") -> Dict[str, Any]:
    logger.warning("Stage 5 audit incomplete for %s: %s", reviewer_name, reason)
    return {
        "reviewer_name": reviewer_name,
        "raw_xml": raw_xml,
        "issues": [],
        "overall_quality": "low",
        "audit_summary": "Audit failed validation.",
        "complete": False,
        "integrity_flags": ["audit_failed"],
        "validation_errors": [reason],
    }
