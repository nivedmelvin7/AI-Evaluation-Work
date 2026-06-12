"""
Stage 8: Deterministic Scoring

Input:  consensus_out (Dict from stage 7)
Output: Dict — full scoring breakdown

Pure Python — NO LLM call.
Temperature: N/A
Self-consistency: No

Implements formulas F1 through F9 exactly as specified.
"""

from typing import Dict, Any

CRITERION_WEIGHTS: Dict[str, float] = {
    "technical_accuracy": 0.18,
    "methodology":        0.15,
    "critical_thinking":  0.14,
    "evidence_quality":   0.12,
    "structure":          0.10,
    "clarity":            0.10,
    "referencing":        0.08,
    "originality":        0.07,
    "professionalism":    0.06,
    # holistic_quality is validation-only — not in the weighted sum
}

CONFIDENCE_TO_UNCERTAINTY: Dict[str, float] = {
    "high":   0.05,
    "medium": 0.20,
    "low":    0.45,
}


def compute_score(consensus_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply formulas F1 through F9.

    F1  Normalise:        s_i = level_i / 4
    F2  Weighted sum:     A   = sum(w_i * s_i)
    F3  Baseline score:   Score = 100 * A
    F4  Uncertainty:      u_i = CONFIDENCE_TO_UNCERTAINTY[confidence]
    F5  Aggregate U:      U = sum(w_i * u_i)
    F6  Penalised score:  Score_pen = Score - (15 * U)
    F7  Conf interval:    [Score_pen - (8*U), Score_pen + (8*U)]
    F8  Non-comp gate:    if s_technical_accuracy < 0.50: cap Score_pen at 49
    F9  Deferral:         if U > 0.25 or any critical criterion confidence == "low"
    """
    results: Dict[str, Any] = {}
    weighted_sum = 0.0
    uncertainty_sum = 0.0

    for criterion, weight in CRITERION_WEIGHTS.items():
        if criterion not in consensus_scores:
            raise ValueError(f"Missing consensus score for: {criterion}")

        level = consensus_scores[criterion]["score"]
        confidence = consensus_scores[criterion]["confidence"].lower()

        s_i = level / 4.0
        u_i = CONFIDENCE_TO_UNCERTAINTY.get(confidence, 0.30)
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

    # F3 Baseline
    baseline_score = round(100 * weighted_sum, 2)

    # F5 Aggregate uncertainty
    U = round(uncertainty_sum, 4)

    # F6 Penalised score
    penalised_score = round(baseline_score - (15 * U), 2)

    # F7 Confidence interval
    margin = round(8 * U, 2)
    interval_low = round(penalised_score - margin, 1)
    interval_high = round(penalised_score + margin, 1)

    # F8 Non-compensatory gate
    gate_triggered = False
    ta_level = consensus_scores.get("technical_accuracy", {}).get("score", 4)
    ta_s_i = ta_level / 4.0
    if ta_s_i < 0.50:  # level < 2
        gate_triggered = True
        penalised_score = min(penalised_score, 49.0)
        interval_low = min(interval_low, 44.0)
        interval_high = min(interval_high, 49.0)

    # F9 Deferral
    critical_criteria = {"technical_accuracy", "methodology"}
    critical_low_confidence = any(
        consensus_scores.get(c, {}).get("confidence", "").lower() == "low"
        for c in critical_criteria
    )
    defer = (U > 0.25) or critical_low_confidence

    final_score = round(penalised_score)
    if defer:
        grade_band = "DEFERRED"
    elif final_score >= 70:
        grade_band = "Distinction"
    elif final_score >= 60:
        grade_band = "Merit"
    elif final_score >= 50:
        grade_band = "Pass"
    else:
        grade_band = "Fail"

    return {
        "criterion_breakdown": results,
        "weighted_sum_A": round(weighted_sum, 4),
        "baseline_score": baseline_score,
        "aggregate_uncertainty_U": U,
        "penalised_score": penalised_score,
        "confidence_interval": [interval_low, interval_high],
        "gate_triggered": gate_triggered,
        "gate_reason": "Technical accuracy below level 2" if gate_triggered else None,
        "deferred": defer,
        "deferral_reason": (
            "Critical criterion confidence is Low" if critical_low_confidence
            else "High aggregate uncertainty" if U > 0.25
            else None
        ),
        "final_score": final_score,
        "grade_band": grade_band,
    }


def run(consensus_out: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the orchestrator. Extracts scores and runs compute_score."""
    scores = consensus_out.get("scores", {})
    return compute_score(scores)
