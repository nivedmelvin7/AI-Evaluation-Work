"""Tests for stage8_scoring deterministic formulas."""

import pytest
from app.pipeline.stage8_scoring import compute_score, CRITERION_WEIGHTS

ALL_WEIGHTED_CRITERIA = list(CRITERION_WEIGHTS.keys())


def _make_scores(level: int, confidence: str = "high") -> dict:
    """Build a consensus_scores dict with uniform level and confidence."""
    scores = {c: {"score": level, "confidence": confidence} for c in ALL_WEIGHTED_CRITERIA}
    # holistic_quality is validation-only but must be present in consensus_out["scores"]
    scores["holistic_quality"] = {"score": level, "confidence": confidence}
    return scores


def test_all_level_4_high_confidence():
    """Perfect scores with high confidence should yield ~100 and Distinction."""
    result = compute_score(_make_scores(4, "high"))
    assert result["grade_band"] == "Distinction"
    assert result["final_score"] >= 95
    assert result["baseline_score"] == 100.0
    assert result["gate_triggered"] is False
    assert result["deferred"] is False


def test_all_level_2_medium_confidence():
    """Mid-range scores should land in Pass territory."""
    result = compute_score(_make_scores(2, "medium"))
    assert result["grade_band"] in ("Pass", "DEFERRED")
    assert 40 <= result["baseline_score"] <= 60


def test_all_level_0():
    """Zero scores should give a Fail (or DEFERRED if uncertainty high)."""
    result = compute_score(_make_scores(0, "low"))
    assert result["final_score"] <= 0 or result["grade_band"] in ("Fail", "DEFERRED")


def test_non_compensatory_gate_triggers():
    """Technical accuracy level 1 (< 2) must cap penalised_score at 49."""
    scores = _make_scores(4, "high")
    scores["technical_accuracy"] = {"score": 1, "confidence": "high"}
    result = compute_score(scores)
    assert result["gate_triggered"] is True
    assert result["penalised_score"] <= 49.0
    assert result["grade_band"] in ("Fail", "DEFERRED")


def test_non_compensatory_gate_level_2_does_not_trigger():
    """Technical accuracy level 2 should NOT trigger the gate."""
    scores = _make_scores(4, "high")
    scores["technical_accuracy"] = {"score": 2, "confidence": "high"}
    result = compute_score(scores)
    assert result["gate_triggered"] is False


def test_deferral_triggered_by_high_uncertainty():
    """Low confidence on all criteria should push aggregate U above 0.25."""
    result = compute_score(_make_scores(3, "low"))
    assert result["deferred"] is True
    assert result["grade_band"] == "DEFERRED"


def test_deferral_triggered_by_critical_low_confidence():
    """Low confidence on technical_accuracy alone must trigger deferral."""
    scores = _make_scores(4, "high")
    scores["technical_accuracy"] = {"score": 4, "confidence": "low"}
    result = compute_score(scores)
    assert result["deferred"] is True
    assert "Critical" in result["deferral_reason"]


def test_confidence_interval_width():
    """Confidence interval should bracket the penalised score by 8*U."""
    result = compute_score(_make_scores(3, "medium"))
    lo, hi = result["confidence_interval"]
    U = result["aggregate_uncertainty_U"]
    expected_margin = round(8 * U, 2)
    assert abs((hi - lo) / 2 - expected_margin) < 0.5


def test_grade_bands():
    """Verify grade band thresholds: >=70 Distinction, >=60 Merit, >=50 Pass."""
    for level, expected_band in [(4, "Distinction"), (3, "Merit"), (2, "Pass")]:
        result = compute_score(_make_scores(level, "high"))
        if not result["deferred"]:
            assert result["grade_band"] == expected_band, (
                f"Level {level} expected {expected_band}, got {result['grade_band']}"
            )


def test_missing_criterion_raises():
    """compute_score must raise ValueError when a weighted criterion is absent."""
    incomplete = {c: {"score": 3, "confidence": "high"} for c in ALL_WEIGHTED_CRITERIA}
    del incomplete["methodology"]
    with pytest.raises(ValueError, match="methodology"):
        compute_score(incomplete)


def test_weighted_sum_formula():
    """Verify F1+F2 by computing the expected weighted sum manually."""
    scores = _make_scores(4, "high")
    result = compute_score(scores)
    expected_A = sum(w * 1.0 for w in CRITERION_WEIGHTS.values())
    assert abs(result["weighted_sum_A"] - expected_A) < 0.001


def test_penalised_score_formula():
    """F6: penalised_score = baseline - 15*U."""
    result = compute_score(_make_scores(4, "medium"))
    expected = result["baseline_score"] - 15 * result["aggregate_uncertainty_U"]
    if not result["gate_triggered"]:
        assert abs(result["penalised_score"] - expected) < 0.01
