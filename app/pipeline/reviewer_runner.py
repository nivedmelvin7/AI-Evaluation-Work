"""Shared reviewer sampling that preserves validated content judgements."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List

from app.config import get_settings
from app.pipeline import compute_median_scores, format_sections_for_prompt, sections_as_document_text
from app.services.llm_service import LLMService
from app.utils.xml_parser import parse_review_assessments, parse_xml_response

logger = logging.getLogger(__name__)


async def run_self_consistent_reviewer(
    *,
    llm: LLMService,
    reviewer_name: str,
    criteria: Iterable[str],
    xml_root_tag: str,
    system_prompt: str,
    user_template: str,
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Run reviewer samples without allowing one malformed response to erase all work.

    Every accepted sample still has complete criterion coverage and valid
    rubric levels.  If at least one such sample is available, its content
    judgement is usable; fewer-than-requested samples are disclosed as a
    quality warning and their confidence is reduced rather than making the
    entire paper ``Not scored``.
    """
    settings = get_settings()
    criteria = tuple(criteria)
    document_text = sections_as_document_text(sections)
    user_prompt = user_template.format(document_sections=format_sections_for_prompt(sections))
    all_scores: List[Dict[str, Dict[str, Any]]] = []
    raw_responses: List[str] = []
    errors: List[str] = []

    for run_number in range(1, settings.self_consistency_runs + 1):
        raw = ""
        run_errors: List[str] = []
        for attempt in range(2):  # initial result plus one corrective retry
            try:
                prompt = user_prompt
                if attempt:
                    issue_text = "; ".join(run_errors[:12]) or "invalid XML or missing required fields"
                    prompt = (
                        f"{user_prompt}\n\nYour previous response was rejected for: {issue_text}. "
                        "Return a corrected complete XML response only; do not invent evidence."
                    )
                raw = await llm.complete_with_retry(
                    system_prompt=system_prompt,
                    user_prompt=prompt,
                    temperature=settings.reviewer_temperature,
                    max_tokens=4096,
                )
            except Exception as exc:
                run_errors = [f"LLM request failed: {exc.__class__.__name__}"]
                continue

            parsed = parse_xml_response(raw, xml_root_tag)
            if parsed is None:
                run_errors = ["response was not valid XML with the required root"]
                continue
            scores, run_errors = parse_review_assessments(
                parsed, criteria, document_text, reviewer_name, run_number
            )
            if not run_errors:
                all_scores.append(scores)
                raw_responses.append(raw)
                break
        else:
            errors.extend(f"run {run_number}: {error}" for error in run_errors)

    successful_runs = len(all_scores)
    if not successful_runs:
        errors.append(
            f"reviewer produced no usable complete assessment after {settings.self_consistency_runs} runs"
        )
        logger.warning("%s reviewer output incomplete: %s", reviewer_name, errors)
        return {
            "reviewer_name": reviewer_name,
            "raw_xml": "",
            "scores": {},
            "complete": False,
            "successful_runs": successful_runs,
            "requested_runs": settings.self_consistency_runs,
            "integrity_flags": ["reviewer_output_incomplete"],
            "validation_errors": errors,
            "quality_warnings": [],
            "sampling_complete": False,
        }

    median_scores = compute_median_scores(all_scores, list(criteria))
    sampling_complete = successful_runs == settings.self_consistency_runs
    quality_warnings = []
    if not sampling_complete:
        quality_warnings = [
            f"{reviewer_name} returned {successful_runs} of {settings.self_consistency_runs} valid samples; confidence was reduced."
        ]
        for assessment in median_scores.values():
            assessment["confidence"] = _lower_confidence(assessment["confidence"])
            assessment["validation_warnings"] = [
                *assessment.get("validation_warnings", []),
                quality_warnings[0],
            ]
        logger.warning("%s reviewer sampling degraded: %s", reviewer_name, quality_warnings[0])
    return {
        "reviewer_name": reviewer_name,
        # Raw output is retained for diagnostics only. `scores` is authoritative.
        "raw_xml": raw_responses[0],
        "scores": median_scores,
        # `complete` means every assigned criterion has a usable assessment;
        # `sampling_complete` records whether all repeat samples succeeded.
        "complete": set(median_scores) == set(criteria),
        "successful_runs": successful_runs,
        "requested_runs": settings.self_consistency_runs,
        "integrity_flags": [],
        "validation_errors": [],
        "quality_warnings": quality_warnings,
        "sampling_complete": sampling_complete,
    }


def _lower_confidence(value: str) -> str:
    return {"high": "medium", "medium": "low", "low": "low"}.get(value.lower(), "low")
