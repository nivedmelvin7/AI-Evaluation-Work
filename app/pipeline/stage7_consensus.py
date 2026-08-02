"""Stage 7: evidence-based consensus with deterministic coverage safeguards."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, List, Tuple

from app.models.assessment import CONFIDENCE_RANK
from app.prompts.stage7_consensus_prompts import CONSENSUS_SYSTEM
from app.rubric import ALL_CRITERIA, RUBRIC_BY_ID
from app.services.llm_service import LLMService
from app.utils.xml_parser import parse_review_assessments, parse_xml_response

logger = logging.getLogger(__name__)


def _reviewers_by_name(*outs: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(output.get("reviewer_name", "")): output for output in outs}


def _serialise_reviewer_output(reviewer_out: Dict[str, Any]) -> Dict[str, Any]:
    """Keep evidence, reasoning, source identity, and integrity in the prompt."""
    return {
        "reviewer_name": reviewer_out.get("reviewer_name"),
        "complete": reviewer_out.get("complete", False),
        "integrity_flags": reviewer_out.get("integrity_flags", []),
        "validation_errors": reviewer_out.get("validation_errors", []),
        "quality_warnings": reviewer_out.get("quality_warnings", []),
        "assessments": reviewer_out.get("final_scores", {}),
    }


def _build_consensus_prompt(reviewer_outputs: Dict[str, Dict[str, Any]]) -> str:
    coverage = {
        criterion: list(RUBRIC_BY_ID[criterion].reviewer_coverage)
        for criterion in ALL_CRITERIA
    }
    multi_criteria = [criterion for criterion in ALL_CRITERIA if len(coverage[criterion]) > 1]
    schema = "\n".join(
        f'''  <criterion id="{criterion}">
    <reasoning>Evidence-based adjudication rationale.</reasoning>
    <evidence><![CDATA[verbatim evidence already supplied by a reviewer]]></evidence>
    <rubric_level_matched>0|1|2|3|4</rubric_level_matched>
    <band_justification>Why this is not the adjacent level above/below where applicable.</band_justification>
    <score>0|1|2|3|4</score>
    <confidence>High|Medium|Low</confidence>
    <confidence_reason>Why this confidence is warranted.</confidence_reason>
  </criterion>'''
        for criterion in multi_criteria
    )
    payload = json.dumps(
        {name: _serialise_reviewer_output(output) for name, output in reviewer_outputs.items()},
        indent=2,
        ensure_ascii=False,
    )
    return f"""Reconcile the multi-reviewer criteria using the complete structured
assessments below. Each assessment includes score, confidence, reasoning,
evidence, band justification, source reviewer, and integrity flags. Do not
invent evidence: reuse an evidence quotation supplied by the reviewer whose
position you adopt.

Reviewer coverage (authoritative):
{json.dumps(coverage, indent=2)}

Complete post-reflection assessments:
{payload}

Only adjudicate these multi-reviewer criteria: {', '.join(multi_criteria)}.
For a disagreement of two or more score levels, choose the better-evidenced
position and reduce confidence by one level. Return exactly this XML:

<consensus>
{schema}
  <deferral_assessment>
    <serious_issue>YES|NO</serious_issue>
    <recommendation>PROCEED|DEFER</recommendation>
    <deferral_reason>Reason only when a serious issue prevents a meaningful assessment; otherwise None.</deferral_reason>
  </deferral_assessment>
</consensus>"""


def _coverage_inputs(
    reviewer_outputs: Dict[str, Dict[str, Any]], criterion: str
) -> tuple[List[Tuple[str, Dict[str, Any]]], List[str]]:
    inputs: List[Tuple[str, Dict[str, Any]]] = []
    errors: List[str] = []
    for reviewer in RUBRIC_BY_ID[criterion].reviewer_coverage:
        output = reviewer_outputs.get(reviewer)
        if not output:
            errors.append(f"{criterion}: required reviewer output is absent: {reviewer}")
            continue
        assessment = output.get("final_scores", {}).get(criterion)
        if not isinstance(assessment, dict):
            errors.append(f"{criterion}: required assessment missing or invalid from {reviewer}")
            continue
        score = assessment.get("score")
        confidence = assessment.get("confidence")
        if (
            isinstance(score, bool)
            or not isinstance(score, int)
            or not 0 <= score <= 4
            or not isinstance(confidence, str)
            or confidence.lower() not in CONFIDENCE_RANK
            or not all(str(assessment.get(field, "")).strip() for field in ("reasoning", "evidence", "band_justification", "confidence_reason"))
        ):
            errors.append(f"{criterion}: required assessment invalid from {reviewer}")
            continue
        inputs.append((reviewer, assessment))
    return inputs, errors


def _carried_forward(
    reviewer: str,
    assessment: Dict[str, Any],
    reviewer_output: Dict[str, Any],
) -> Dict[str, Any]:
    result = dict(assessment)
    result.update({
        "consensus_rationale": "Single-reviewer criterion carried forward unchanged.",
        "reviewer_contributors": [reviewer],
        "reviewer_integrity_flags": list(reviewer_output.get("integrity_flags", [])),
    })
    return result


def _single_source_content_score(
    criterion: str,
    reviewer: str,
    assessment: Dict[str, Any],
    reviewer_output: Dict[str, Any],
) -> Dict[str, Any]:
    """Keep a usable judgement when a secondary reviewer is unavailable."""
    result = _carried_forward(reviewer, assessment, reviewer_output)
    result["confidence"] = _lower_confidence(str(result.get("confidence", "low")))
    result["consensus_rationale"] = (
        "Content-based carry-forward from the available reviewer; "
        "confidence reduced because no second reviewer was available."
    )
    result["validation_warnings"] = [
        *result.get("validation_warnings", []),
        f"{criterion}: only {reviewer} supplied a usable assessment.",
    ]
    return result


def _lower_confidence(value: str) -> str:
    return {"high": "medium", "medium": "low", "low": "low"}.get(value.lower(), "low")


def _deterministic_provisional_multi(
    inputs: List[Tuple[str, Dict[str, Any]]], reason: str
) -> Dict[str, Any]:
    reviewer, assessment = min(
        inputs,
        key=lambda item: (-CONFIDENCE_RANK.get(str(item[1].get("confidence", "low")).lower(), 0), item[0]),
    )
    result = dict(assessment)
    result.update({
        "consensus_rationale": f"Provisional deterministic carry-forward: {reason}",
        "reviewer_contributors": [name for name, _ in inputs],
        "reviewer_integrity_flags": ["consensus_failed_validation"],
    })
    return result


async def run(
    llm: LLMService,
    de_final: Dict[str, Any],
    meth_final: Dict[str, Any],
    comm_final: Dict[str, Any],
    document_text: str = "",
) -> Dict[str, Any]:
    """Reconcile available evidence without discarding usable content scores."""
    reviewer_outputs = _reviewers_by_name(de_final, meth_final, comm_final)
    scores: Dict[str, Dict[str, Any]] = {}
    quality_warnings: List[str] = []
    multi_inputs: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}

    for criterion in ALL_CRITERIA:
        inputs, errors = _coverage_inputs(reviewer_outputs, criterion)
        quality_warnings.extend(errors)
        if not inputs:
            continue
        for reviewer, _ in inputs:
            reviewer_output = reviewer_outputs[reviewer]
            if not reviewer_output.get("complete"):
                quality_warnings.append(
                    f"{criterion}: {reviewer} assessment was carried forward after a review-stage issue: "
                    + "; ".join(reviewer_output.get("validation_errors", []))
                )
        if len(inputs) == 1:
            reviewer, assessment = inputs[0]
            if len(RUBRIC_BY_ID[criterion].reviewer_coverage) > 1:
                scores[criterion] = _single_source_content_score(
                    criterion, reviewer, assessment, reviewer_outputs[reviewer]
                )
            else:
                scores[criterion] = _carried_forward(reviewer, assessment, reviewer_outputs[reviewer])
        else:
            multi_inputs[criterion] = inputs

    raw = ""
    consensus_validation_errors: List[str] = []
    parsed_scores: Dict[str, Dict[str, Any]] = {}
    if multi_inputs:
        try:
            raw = await llm.complete_with_retry(
                system_prompt=CONSENSUS_SYSTEM,
                user_prompt=_build_consensus_prompt(reviewer_outputs),
                temperature=0.0,
                max_tokens=4096,
            )
            parsed = parse_xml_response(raw, "consensus")
            if parsed is None:
                consensus_validation_errors.append("consensus response was not valid XML")
            else:
                parsed_scores, consensus_validation_errors = parse_review_assessments(
                    parsed, multi_inputs.keys(), document_text, "Consensus", 1
                )
        except Exception as exc:
            consensus_validation_errors.append(f"consensus LLM request failed: {exc.__class__.__name__}")

    if consensus_validation_errors:
        quality_warnings.extend(consensus_validation_errors)
        for criterion, inputs in multi_inputs.items():
            scores[criterion] = _deterministic_provisional_multi(
                inputs, "; ".join(consensus_validation_errors)
            )
    else:
        for criterion, consensus_assessment in parsed_scores.items():
            inputs = multi_inputs[criterion]
            input_scores = [assessment["score"] for _, assessment in inputs]
            result = dict(consensus_assessment)
            if max(input_scores) - min(input_scores) >= 2:
                result["confidence"] = _lower_confidence(result["confidence"])
            result.update({
                "consensus_rationale": result["reasoning"],
                "reviewer_contributors": [reviewer for reviewer, _ in inputs],
                "reviewer_integrity_flags": [],
            })
            scores[criterion] = result

    deferral_reasons: List[str] = []
    recommendation = "PROCEED"
    serious_issue = False
    if raw and not consensus_validation_errors:
        parsed = parse_xml_response(raw, "consensus")
        if parsed is not None:
            serious_issue_text = (parsed.findtext("deferral_assessment/serious_issue") or "NO").strip().upper()
            recommendation_text = (parsed.findtext("deferral_assessment/recommendation") or "PROCEED").strip().upper()
            reason = (parsed.findtext("deferral_assessment/deferral_reason") or "").strip()
            serious_issue = serious_issue_text == "YES"
            if serious_issue and recommendation_text == "DEFER" and reason:
                deferral_reasons.append(f"Consensus evidence-based deferral: {reason}")
                recommendation = "DEFER"

    return {
        "raw_xml": raw,
        "scores": scores,
        "complete": set(scores) == set(ALL_CRITERIA),
        "integrity_flags": [],
        "validation_errors": [],
        "quality_warnings": quality_warnings,
        "deferral_assessment": {
            "recommendation": recommendation,
            "deferral_reason": "; ".join(deferral_reasons) if deferral_reasons else None,
            "serious_issue": serious_issue,
        },
    }
