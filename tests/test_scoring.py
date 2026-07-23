"""Regression tests for the deterministic Stage 8 scoring policy."""

import pytest

from app.pipeline.stage8_scoring import CRITERION_WEIGHTS, compute_score, run


ALL_WEIGHTED_CRITERIA = list(CRITERION_WEIGHTS)


def _make_scores(level: int, confidence: str = "high", holistic_level: int | None = None) -> dict:
    scores = {criterion: {"score": level, "confidence": confidence} for criterion in ALL_WEIGHTED_CRITERIA}
    scores["holistic_quality"] = {
        "score": level if holistic_level is None else holistic_level,
        "confidence": confidence,
    }
    return scores


def test_weights_match_published_rubric_and_sum_to_one():
    assert CRITERION_WEIGHTS["structure"] == 0.12
    assert CRITERION_WEIGHTS["professionalism"] == 0.04
    assert sum(CRITERION_WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("level", "expected_score", "expected_band"),
    [(4, 100, "Distinction"), (3, 75, "Merit"), (2, 50, "Pass")],
)
def test_uniform_rubric_levels_map_to_their_intended_grade_bands(level, expected_score, expected_band):
    result = compute_score(_make_scores(level))
    assert result["achievement_score"] == float(expected_score)
    assert result["final_score"] == expected_score
    assert result["grade_band"] == expected_band
    assert result["deferred"] is False


def test_confidence_does_not_reduce_the_achievement_score():
    high = compute_score(_make_scores(3, "high"))
    medium = compute_score(_make_scores(3, "medium"))
    assert high["achievement_score"] == medium["achievement_score"] == 75.0
    assert high["final_score"] == medium["final_score"] == 75
    assert high["aggregate_uncertainty_U"] < medium["aggregate_uncertainty_U"]


def test_score_and_uncertainty_band_are_bounded():
    result = compute_score(_make_scores(0, "low"))
    assert result["final_score"] == 0
    assert result["uncertainty_band"][0] == 0.0
    assert all(0 <= value <= 100 for value in result["uncertainty_band"])
    assert result["grade_band"] == "DEFERRED"


def test_technical_accuracy_floor_caps_the_final_score():
    scores = _make_scores(4)
    scores["technical_accuracy"] = {"score": 1, "confidence": "high"}
    result = compute_score(scores)
    assert result["gate_triggered"] is True
    assert result["final_score"] == 49
    assert "Technical accuracy" in result["gate_reason"]
    assert result["uncertainty_band"][1] <= 49


def test_methodology_floor_caps_the_final_score():
    scores = _make_scores(4)
    scores["methodology"] = {"score": 1, "confidence": "high"}
    result = compute_score(scores)
    assert result["gate_triggered"] is True
    assert result["final_score"] == 49
    assert "Methodology" in result["gate_reason"]


def test_deferral_is_triggered_by_critical_low_confidence():
    scores = _make_scores(4)
    scores["technical_accuracy"] = {"score": 4, "confidence": "low"}
    result = compute_score(scores)
    assert result["deferred"] is True
    assert result["grade_band"] == "DEFERRED"
    assert "Critical" in result["deferral_reason"]


def test_consensus_deferral_recommendation_is_honoured():
    result = run({
        "scores": _make_scores(4),
        "deferral_assessment": {"recommendation": "DEFER", "deferral_reason": "Evidence needs human review"},
    })
    assert result["deferred"] is True
    assert result["grade_band"] == "DEFERRED"
    assert "Evidence needs human review" in result["deferral_reason"]


def test_holistic_disagreement_requires_moderation_without_changing_score():
    result = compute_score(_make_scores(3, holistic_level=4))
    assert result["grade_band"] == "Merit"
    assert result["holistic_validation"] == {
        "available": True,
        "level": 4,
        "expected_grade_band": "Distinction",
        "calculated_grade_band": "Merit",
        "requires_moderation": True,
    }


def test_missing_or_invalid_weighted_scores_are_rejected():
    incomplete = _make_scores(3)
    del incomplete["methodology"]
    with pytest.raises(ValueError, match="methodology"):
        compute_score(incomplete)

    invalid = _make_scores(3)
    invalid["clarity"] = {"score": 5, "confidence": "high"}
    with pytest.raises(ValueError, match="clarity"):
        compute_score(invalid)
