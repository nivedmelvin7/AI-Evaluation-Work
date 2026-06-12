"""
Stage 7: Consensus Reconciliation

Input:  llm (LLMService),
        de_final   (Dict from stage 6 — Domain Expert),
        meth_final (Dict from stage 6 — Methodologist),
        comm_final (Dict from stage 6 — Communication Specialist)
Output: Dict with keys:
          raw_xml            (str)
          scores             (Dict) — {criterion: {score, confidence}}
          deferral_assessment (Dict)

Temperature: 0.0 (deterministic)
Self-consistency: No
"""

import sys
from typing import Dict, Any

from app.services.llm_service import LLMService
from app.prompts.templates import CONSENSUS_SYSTEM
from app.utils.xml_parser import parse_xml_response

ALL_CRITERIA = [
    "technical_accuracy",
    "methodology",
    "evidence_quality",
    "critical_thinking",
    "structure",
    "clarity",
    "referencing",
    "originality",
    "professionalism",
    "holistic_quality",
]


def _format_reviewer_scores(reviewer_out: Dict[str, Any]) -> str:
    lines = []
    for criterion, data in reviewer_out.get("final_scores", {}).items():
        score = data.get("score", "N/A")
        confidence = data.get("confidence", "medium")
        lines.append(f"  {criterion}: score={score}, confidence={confidence}")
    return "\n".join(lines) if lines else "  (no scores available)"


def _build_consensus_prompt(
    de_final: Dict[str, Any],
    meth_final: Dict[str, Any],
    comm_final: Dict[str, Any],
) -> str:
    de_text = _format_reviewer_scores(de_final)
    meth_text = _format_reviewer_scores(meth_final)
    comm_text = _format_reviewer_scores(comm_final)

    criteria_xml = ""
    for crit in ALL_CRITERIA:
        criteria_xml += f"""  <criterion id="{crit}">
    <reviewer_scores>Fill in scores from input above for this criterion</reviewer_scores>
    <agreement_level>Strong|Moderate|Weak</agreement_level>
    <adjudication>Reason for the chosen final score.</adjudication>
    <final_score>0|1|2|3|4</final_score>
    <final_confidence>High|Medium|Low</final_confidence>
  </criterion>\n"""

    return f"""Reconcile these post-reflection scores from three specialist reviewers.

Domain Expert final scores:
{de_text}

Methodologist final scores:
{meth_text}

Communication Specialist final scores:
{comm_text}

Coverage rules:
- technical_accuracy: Domain Expert (primary), Methodologist (secondary)
- methodology: Domain Expert + Methodologist (joint)
- evidence_quality: Domain Expert + Methodologist (joint)
- critical_thinking: Methodologist (primary)
- structure, clarity, referencing, originality, professionalism, holistic_quality: Communication Specialist (primary)

Adjudication rules:
- Agreement = scores within 1 point → keep higher-confidence score
- Disagreement = 2+ point gap → adopt better-evidenced position, reduce final_confidence by one level
- If only one reviewer covers a criterion, use their score directly

Return this exact XML with all 10 criteria filled in:

<consensus>
{criteria_xml}  <deferral_assessment>
    <any_low_confidence_critical>Yes|No</any_low_confidence_critical>
    <recommendation>PROCEED|DEFER</recommendation>
    <deferral_reason>Which criteria triggered deferral, if any. Otherwise: None.</deferral_reason>
  </deferral_assessment>
</consensus>"""


async def run(
    llm: LLMService,
    de_final: Dict[str, Any],
    meth_final: Dict[str, Any],
    comm_final: Dict[str, Any],
) -> Dict[str, Any]:
    """Reconcile post-reflection reviewer scores into a single consensus."""
    user_prompt = _build_consensus_prompt(de_final, meth_final, comm_final)

    try:
        raw = await llm.complete_with_retry(
            system_prompt=CONSENSUS_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception as e:
        print(f"[Stage 7] LLM call failed: {e}", file=sys.stderr)
        return _fallback_consensus(de_final, meth_final, comm_final)

    parsed = parse_xml_response(raw, "consensus")

    scores: Dict[str, Dict[str, Any]] = {}
    deferral_assessment: Dict[str, Any] = {"recommendation": "PROCEED", "deferral_reason": None}

    if parsed is not None:
        for criterion_el in parsed.findall(".//criterion"):
            criterion_id = criterion_el.get("id", "").strip()
            final_score_el = criterion_el.find("final_score")
            final_confidence_el = criterion_el.find("final_confidence")

            if criterion_id:
                try:
                    score = int(final_score_el.text.strip()) if final_score_el is not None and final_score_el.text else 2
                except (ValueError, TypeError):
                    score = 2
                confidence = (
                    final_confidence_el.text.strip().lower()
                    if final_confidence_el is not None and final_confidence_el.text
                    else "medium"
                )
                scores[criterion_id] = {
                    "score": max(0, min(4, score)),
                    "confidence": confidence,
                }

        deferral_el = parsed.find("deferral_assessment")
        if deferral_el is not None:
            rec_el = deferral_el.find("recommendation")
            reason_el = deferral_el.find("deferral_reason")
            deferral_assessment = {
                "recommendation": rec_el.text.strip() if rec_el is not None and rec_el.text else "PROCEED",
                "deferral_reason": reason_el.text.strip() if reason_el is not None and reason_el.text else None,
            }
    else:
        print("[Stage 7] XML parse failed — using fallback consensus.", file=sys.stderr)
        return _fallback_consensus(de_final, meth_final, comm_final)

    # Fill any missing criteria from reviewer scores
    all_reviewer_final = {}
    for reviewer_out in [de_final, meth_final, comm_final]:
        for crit, data in reviewer_out.get("final_scores", {}).items():
            if crit not in all_reviewer_final:
                all_reviewer_final[crit] = data

    for crit in ALL_CRITERIA:
        if crit not in scores:
            fallback = all_reviewer_final.get(crit, {"score": 2, "confidence": "low"})
            scores[crit] = {"score": fallback["score"], "confidence": "low"}

    return {
        "raw_xml": raw,
        "scores": scores,
        "deferral_assessment": deferral_assessment,
    }


def _fallback_consensus(
    de_final: Dict[str, Any],
    meth_final: Dict[str, Any],
    comm_final: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a simple fallback consensus from available reviewer scores."""
    merged: Dict[str, Dict[str, Any]] = {}
    for reviewer_out in [de_final, meth_final, comm_final]:
        for crit, data in reviewer_out.get("final_scores", {}).items():
            if crit not in merged:
                merged[crit] = {"score": data["score"], "confidence": "low"}

    for crit in ALL_CRITERIA:
        if crit not in merged:
            merged[crit] = {"score": 2, "confidence": "low"}

    return {
        "raw_xml": "",
        "scores": merged,
        "deferral_assessment": {
            "recommendation": "DEFER",
            "deferral_reason": "Consensus LLM call failed — scores are unverified fallbacks.",
        },
    }
