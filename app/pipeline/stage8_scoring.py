"""Deterministic F1--F9 scoring and explicit deferred-result semantics."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from app.rubric import CRITICAL_CRITERIA, CRITERION_WEIGHTS, WEIGHTED_CRITERIA


CONFIDENCE_TO_UNCERTAINTY: Dict[str, float] = {
    "high": 0.05,
    "medium": 0.20,
    "low": 0.45,
}
CRITICAL_FLOOR_CRITERIA = set(CRITICAL_CRITERIA)  # backwards-compatible export
HOLISTIC_GRADE_BANDS = {4: "Distinction", 3: "Merit", 2: "Pass", 1: "Fail", 0: "Fail"}


def _validated_level(data: Dict[str, Any], criterion: str) -> int:
    level = data.get("score")
    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 4:
        raise ValueError(f"Invalid score for {criterion}: expected an integer from 0 to 4")
    return level


def _validated_confidence(data: Dict[str, Any], criterion: str) -> str:
    confidence = data.get("confidence")
    if not isinstance(confidence, str) or confidence.strip().lower() not in CONFIDENCE_TO_UNCERTAINTY:
        raise ValueError(f"Invalid confidence for {criterion}: expected High, Medium, or Low")
    return confidence.strip().lower()


def _grade_band(score: float) -> str:
    """Use the unrounded policy score so display rounding never changes a band."""
    if score >= 80:
        return "Distinction"
    if score >= 65:
        return "Merit"
    if score >= 50:
        return "Pass"
    return "Fail"


def _holistic_validation(scores: Dict[str, Dict[str, Any]], policy_band: Optional[str]) -> Dict[str, Any]:
    holistic = scores.get("holistic_quality")
    if not isinstance(holistic, dict):
        return {"available": False, "requires_moderation": False, "reason": "Holistic quality was not assessed."}
    try:
        level = _validated_level(holistic, "holistic_quality")
        _validated_confidence(holistic, "holistic_quality")
    except ValueError as exc:
        return {"available": False, "requires_moderation": False, "reason": str(exc)}
    if policy_band is None:
        return {
            "available": True,
            "level": level,
            "expected_grade_band": HOLISTIC_GRADE_BANDS[level],
            "calculated_grade_band": None,
            "requires_moderation": False,
        }
    expected = HOLISTIC_GRADE_BANDS[level]
    return {
        "available": True,
        "level": level,
        "expected_grade_band": expected,
        "calculated_grade_band": policy_band,
        "requires_moderation": expected != policy_band,
    }


def _incomplete_result(
    breakdown: Dict[str, Dict[str, Any]],
    reasons: List[str],
    scores: Dict[str, Dict[str, Any]],
    missing_criteria: List[str],
    coverage_weight: float,
) -> Dict[str, Any]:
    return {
        "criterion_breakdown": breakdown,
        "weighted_sum_A": None,
        "baseline_score": None,
        "achievement_score": None,
        "final_policy_score": None,
        "aggregate_uncertainty_U": None,
        "achievement_uncertainty_band": None,
        "uncertainty_band": None,
        "gate_triggered": False,
        "gate_reason": None,
        "scoring_complete": False,
        "content_based_estimate": False,
        "assessment_coverage_weight": round(coverage_weight, 4),
        "missing_criteria": missing_criteria,
        "deferred": True,
        "deferral_reasons": reasons,
        "deferral_reason": "; ".join(reasons),
        "holistic_validation": _holistic_validation(scores, None),
        "final_score": None,
        "provisional_score": None,
        "provisional_grade_band": None,
        "grade_band": "DEFERRED",
    }


def compute_score(
    consensus_scores: Dict[str, Dict[str, Any]],
    consensus_deferral: Optional[Dict[str, Any]] = None,
    integrity_failures: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Apply the rubric to the content that has actually been assessed.

    F1 ``s_i = level_i / 4``
    F2 ``A = sum(w_i * s_i)``
    F3 ``achievement_score = 100 * A``
    F4 ``u_i = High .05, Medium .20, Low .45``
    F5 ``U = sum(w_i * u_i)``
    F6 ``[max(0, achievement_score - 8U), min(100, achievement_score + 8U)]``
    F7 applies the two critical criterion gate to create ``final_policy_score``.
    F8 reserves deferral for serious integrity/content-assessability failures.
    F9 compares validation-only holistic quality with the policy grade.
    """
    consensus_scores = consensus_scores or {}
    breakdown: Dict[str, Dict[str, Any]] = {}
    invalid_reasons: List[str] = []
    weighted_sum = 0.0
    uncertainty_sum = 0.0
    levels: Dict[str, int] = {}
    confidences: Dict[str, str] = {}

    for criterion in WEIGHTED_CRITERIA:
        data = consensus_scores.get(criterion)
        if not isinstance(data, dict):
            invalid_reasons.append(f"Missing weighted criterion: {criterion}")
            continue
        try:
            level = _validated_level(data, criterion)
            confidence = _validated_confidence(data, criterion)
        except ValueError as exc:
            invalid_reasons.append(str(exc))
            continue
        levels[criterion] = level
        confidences[criterion] = confidence
        s_i = level / 4.0
        u_i = CONFIDENCE_TO_UNCERTAINTY[confidence]
        contribution = CRITERION_WEIGHTS[criterion] * s_i
        uncertainty_contribution = CRITERION_WEIGHTS[criterion] * u_i
        weighted_sum += contribution
        uncertainty_sum += uncertainty_contribution
        breakdown[criterion] = {
            "level": level,
            "s_i": round(s_i, 4),
            "weight": CRITERION_WEIGHTS[criterion],
            "contribution": round(contribution, 4),
            "confidence": confidence,
            "u_i": u_i,
            "confidence_risk": u_i,
            "uncertainty_contribution": round(uncertainty_contribution, 4),
            "evidence": data.get("evidence"),
            "reasoning": data.get("reasoning"),
            "band_justification": data.get("band_justification"),
            "consensus_rationale": data.get("consensus_rationale"),
        }

    missing_criteria = [criterion for criterion in WEIGHTED_CRITERIA if criterion not in levels]
    coverage_weight = sum(CRITERION_WEIGHTS[criterion] for criterion in levels)
    core_criteria_available = set(CRITICAL_CRITERIA).issubset(levels)
    if not core_criteria_available or coverage_weight < 0.5:
        reasons = list(invalid_reasons)
        if not core_criteria_available:
            missing_core = sorted(set(CRITICAL_CRITERIA) - set(levels))
            reasons.append("Core criteria could not be assessed: " + ", ".join(missing_core))
        if coverage_weight < 0.5:
            reasons.append("Too little of the weighted rubric has usable content evidence")
        return _incomplete_result(
            breakdown,
            reasons,
            consensus_scores,
            missing_criteria,
            coverage_weight,
        )

    # If a non-core criterion is unavailable, score the content that *was*
    # assessed rather than turning a successful evaluation into "Not scored".
    # The result remains explicitly marked as a content-based estimate.
    achievement_raw = 100 * (weighted_sum / coverage_weight)
    policy_raw = achievement_raw
    gate_reasons: List[str] = []
    if levels["technical_accuracy"] < 2:
        gate_reasons.append("Technical accuracy below level 2")
    if levels["methodology"] < 2:
        gate_reasons.append("Methodology below level 2")
    if gate_reasons:
        policy_raw = min(achievement_raw, 49.0)
    policy_band = _grade_band(policy_raw)
    U = uncertainty_sum / coverage_weight
    # F6 is deliberately centred on F3 achievement, never on gate-adjusted or display-rounded score.
    uncertainty_band = [
        round(max(0.0, achievement_raw - 8 * U), 2),
        round(min(100.0, achievement_raw + 8 * U), 2),
    ]

    consensus_deferral = consensus_deferral or {}
    integrity_reasons = [str(reason) for reason in (integrity_failures or []) if str(reason).strip()]
    consensus_reason = consensus_deferral.get("deferral_reason")
    consensus_recommends_deferral = (
        str(consensus_deferral.get("recommendation", "")).upper() == "DEFER"
        and consensus_deferral.get("serious_issue") is True
    )
    deferral_reasons = list(integrity_reasons)
    if consensus_recommends_deferral:
        deferral_reasons.append(str(consensus_reason or "Consensus carries an evidence-based deferral reason"))
    deferred = bool(deferral_reasons)
    achievement_score = round(achievement_raw, 2)
    final_policy_score = round(policy_raw, 2)

    return {
        "criterion_breakdown": breakdown,
        "weighted_sum_A": round(weighted_sum / coverage_weight, 4),
        "baseline_score": achievement_score,
        "achievement_score": achievement_score,
        "final_policy_score": final_policy_score,
        "aggregate_uncertainty_U": round(U, 4),
        "achievement_uncertainty_band": uncertainty_band,
        "uncertainty_band": uncertainty_band,  # compatibility alias for existing UI/export clients
        "gate_triggered": bool(gate_reasons),
        "gate_reason": "; ".join(gate_reasons) if gate_reasons else None,
        "scoring_complete": not invalid_reasons,
        "content_based_estimate": bool(invalid_reasons),
        "assessment_coverage_weight": round(coverage_weight, 4),
        "missing_criteria": missing_criteria,
        "deferred": deferred,
        "deferral_reasons": deferral_reasons,
        "deferral_reason": "; ".join(deferral_reasons) if deferral_reasons else None,
        "holistic_validation": _holistic_validation(consensus_scores, policy_band),
        # A serious deferral keeps the calculated result available only as a
        # clearly labelled provisional value.
        "final_score": None if deferred else final_policy_score,
        "provisional_score": final_policy_score if deferred else None,
        "provisional_grade_band": policy_band if deferred else None,
        "grade_band": "DEFERRED" if deferred else policy_band,
    }


def run(consensus_out: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the orchestrator."""
    return compute_score(
        consensus_out.get("scores", {}),
        consensus_out.get("deferral_assessment"),
        consensus_out.get("serious_failures", []),
    )
