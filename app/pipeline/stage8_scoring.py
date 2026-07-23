"""Deterministic, policy-based scoring for the document evaluation pipeline."""

from typing import Any, Dict, Optional


# These weights are the published rubric weights. Keep this as the source used
# for calculation and keep rubric_backbone.py in sync when the policy changes.
CRITERION_WEIGHTS: Dict[str, float] = {
    "technical_accuracy": 0.18,
    "methodology": 0.15,
    "critical_thinking": 0.14,
    "evidence_quality": 0.12,
    "structure": 0.12,
    "clarity": 0.10,
    "referencing": 0.08,
    "originality": 0.07,
    "professionalism": 0.04,
}

CONFIDENCE_TO_UNCERTAINTY: Dict[str, float] = {
    "high": 0.05,
    "medium": 0.20,
    "low": 0.45,
}

CRITICAL_FLOOR_CRITERIA = {"technical_accuracy", "methodology"}
HOLISTIC_GRADE_BANDS = {4: "Distinction", 3: "Merit", 2: "Pass", 1: "Fail", 0: "Fail"}


def _validated_level(data: Dict[str, Any], criterion: str) -> int:
    """Return a rubric level only when it is a whole number on the 0--4 scale."""
    level = data.get("score")
    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 4:
        raise ValueError(f"Invalid score for {criterion}: expected an integer from 0 to 4")
    return level


def _validated_confidence(data: Dict[str, Any], criterion: str) -> str:
    confidence = data.get("confidence")
    if not isinstance(confidence, str) or confidence.lower() not in CONFIDENCE_TO_UNCERTAINTY:
        raise ValueError(f"Invalid confidence for {criterion}: expected high, medium, or low")
    return confidence.lower()


def _grade_band(score: int) -> str:
    """Map the 0--100 scale to bands consistent with the 0--4 rubric labels."""
    if score >= 80:
        return "Distinction"
    if score >= 65:
        return "Merit"
    if score >= 50:
        return "Pass"
    return "Fail"


def compute_score(
    consensus_scores: Dict[str, Dict[str, Any]],
    consensus_deferral: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate achievement, confidence risk, gates, and moderation flags.

    F1  Normalise:           s_i = level_i / 4
    F2  Weighted sum:        A = sum(w_i * s_i)
    F3  Achievement score:   Score = 100 * A
    F4  Confidence mapping:  u_i = {high: 0.05, medium: 0.20, low: 0.45}
    F5  Aggregate risk:      U = sum(w_i * u_i)
    F6  Uncertainty band:    Score +/- 8U, bounded to the valid score range
    F7  Critical floors:     technical accuracy or methodology below level 2
                              caps the score at 49
    F8  Deferral:            high aggregate risk, low confidence in a critical
                              criterion, or a consensus deferral recommendation
    F9  Holistic validation: disagreement with the validation-only holistic
                              grade band requires moderation, not an automatic
                              score adjustment.

    Confidence never reduces the achievement score. It instead informs the
    uncertainty band and whether the result must be deferred for review.
    """
    results: Dict[str, Any] = {}
    weighted_sum = 0.0
    uncertainty_sum = 0.0
    levels: Dict[str, int] = {}
    confidences: Dict[str, str] = {}

    for criterion, weight in CRITERION_WEIGHTS.items():
        if criterion not in consensus_scores:
            raise ValueError(f"Missing consensus score for: {criterion}")

        data = consensus_scores[criterion]
        level = _validated_level(data, criterion)
        confidence = _validated_confidence(data, criterion)
        levels[criterion] = level
        confidences[criterion] = confidence

        s_i = level / 4.0
        u_i = CONFIDENCE_TO_UNCERTAINTY[confidence]
        contribution = weight * s_i
        uncertainty_contribution = weight * u_i

        weighted_sum += contribution
        uncertainty_sum += uncertainty_contribution
        results[criterion] = {
            "level": level,
            "s_i": round(s_i, 4),
            "weight": weight,
            "contribution": round(contribution, 4),
            "confidence": confidence,
            "u_i": u_i,
            "uncertainty_contribution": round(uncertainty_contribution, 4),
        }

    baseline_score = round(max(0.0, min(100.0, 100 * weighted_sum)), 2)
    U = round(uncertainty_sum, 4)

    gate_reasons = []
    if levels["technical_accuracy"] < 2:
        gate_reasons.append("Technical accuracy below level 2")
    if levels["methodology"] < 2:
        gate_reasons.append("Methodology below level 2")
    gate_triggered = bool(gate_reasons)

    final_score = round(baseline_score)
    if gate_triggered:
        final_score = min(final_score, 49)
    final_score = max(0, min(100, final_score))
    preliminary_grade_band = _grade_band(final_score)

    # This is a policy transparency range, not a statistically calibrated CI.
    margin = 8 * U
    upper_bound = 49.0 if gate_triggered else 100.0
    uncertainty_band = [
        round(max(0.0, final_score - margin), 1),
        round(min(upper_bound, final_score + margin), 1),
    ]

    critical_low_confidence = any(confidences[c] == "low" for c in CRITICAL_FLOOR_CRITERIA)
    consensus_deferral = consensus_deferral or {}
    consensus_recommends_deferral = str(consensus_deferral.get("recommendation", "")).upper() == "DEFER"
    consensus_reason = consensus_deferral.get("deferral_reason")
    defer = (U > 0.25) or critical_low_confidence or consensus_recommends_deferral

    deferral_reasons = []
    if critical_low_confidence:
        deferral_reasons.append("Critical criterion confidence is Low")
    if U > 0.25:
        deferral_reasons.append("High aggregate uncertainty")
    if consensus_recommends_deferral:
        deferral_reasons.append(str(consensus_reason or "Consensus recommends deferral"))

    holistic_validation: Dict[str, Any] = {"available": False, "requires_moderation": False}
    holistic_data = consensus_scores.get("holistic_quality")
    if holistic_data is not None:
        holistic_level = _validated_level(holistic_data, "holistic_quality")
        expected_band = HOLISTIC_GRADE_BANDS[holistic_level]
        holistic_validation = {
            "available": True,
            "level": holistic_level,
            "expected_grade_band": expected_band,
            "calculated_grade_band": preliminary_grade_band,
            "requires_moderation": expected_band != preliminary_grade_band,
        }

    return {
        "criterion_breakdown": results,
        "weighted_sum_A": round(weighted_sum, 4),
        "baseline_score": baseline_score,
        "achievement_score": baseline_score,
        "aggregate_uncertainty_U": U,
        "uncertainty_band": uncertainty_band,
        "gate_triggered": gate_triggered,
        "gate_reason": "; ".join(gate_reasons) if gate_reasons else None,
        "deferred": defer,
        "deferral_reason": "; ".join(deferral_reasons) if deferral_reasons else None,
        "holistic_validation": holistic_validation,
        "final_score": final_score,
        "grade_band": "DEFERRED" if defer else preliminary_grade_band,
    }


def run(consensus_out: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the orchestrator."""
    return compute_score(
        consensus_out.get("scores", {}),
        consensus_out.get("deferral_assessment"),
    )
