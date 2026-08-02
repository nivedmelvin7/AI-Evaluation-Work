"""Regression tests for deterministic F1--F9 scoring semantics."""

import pytest

from app.pipeline.stage8_scoring import CRITERION_WEIGHTS, compute_score, run
from app.rubric import CRITICAL_CRITERIA, WEIGHTED_CRITERIA


def _make_scores(level: int, confidence: str = "high", holistic_level: int | None = None) -> dict:
    scores = {criterion: {"score": level, "confidence": confidence} for criterion in WEIGHTED_CRITERIA}
    scores["holistic_quality"] = {
        "score": level if holistic_level is None else holistic_level,
        "confidence": confidence,
    }
    return scores


def test_authoritative_weights_are_exact_and_holistic_is_excluded():
    assert CRITERION_WEIGHTS == {
        "technical_accuracy": 0.18, "methodology": 0.15, "critical_thinking": 0.14,
        "evidence_quality": 0.12, "structure": 0.12, "clarity": 0.10,
        "referencing": 0.08, "originality": 0.07, "professionalism": 0.04,
    }
    assert sum(CRITERION_WEIGHTS.values()) == pytest.approx(1.0)
    assert "holistic_quality" not in CRITERION_WEIGHTS
    assert set(CRITICAL_CRITERIA) == {"technical_accuracy", "methodology"}


@pytest.mark.parametrize(
    ("level", "expected_score", "expected_band"),
    [(0, 0.0, "Fail"), (1, 25.0, "Fail"), (2, 50.0, "Pass"), (3, 75.0, "Merit"), (4, 100.0, "Distinction")],
)
def test_uniform_rubric_levels_map_correctly(level, expected_score, expected_band):
    result = compute_score(_make_scores(level))
    assert result["achievement_score"] == expected_score
    assert result["final_policy_score"] == (min(expected_score, 49.0) if level < 2 else expected_score)
    assert result["grade_band"] == expected_band
    assert result["deferred"] is False


def test_confidence_risk_values_inform_the_band_without_hiding_a_content_score():
    assert compute_score(_make_scores(3, "high"))["aggregate_uncertainty_U"] == pytest.approx(0.05)
    medium = compute_score(_make_scores(3, "medium"))
    assert medium["aggregate_uncertainty_U"] == pytest.approx(0.20)
    assert medium["deferred"] is False  # exactly/under .25 does not defer
    low = compute_score(_make_scores(3, "low"))
    assert low["aggregate_uncertainty_U"] == pytest.approx(0.45)
    assert low["deferred"] is False
    assert low["final_score"] == 75.0


def test_uncertainty_exactly_point_25_does_not_defer(monkeypatch):
    # The comparison itself is strict even if policy weights normally do not
    # create this exact aggregate value.
    from app.pipeline import stage8_scoring

    monkeypatch.setitem(stage8_scoring.CONFIDENCE_TO_UNCERTAINTY, "medium", 0.25)
    result = compute_score(_make_scores(3, "medium"))
    assert result["aggregate_uncertainty_U"] == 0.25
    assert result["deferred"] is False


def test_gate_does_not_recentre_f6_band():
    scores = _make_scores(4)
    scores["technical_accuracy"] = {"score": 1, "confidence": "high"}
    result = compute_score(scores)
    assert result["gate_triggered"] is True
    assert result["final_policy_score"] == 49.0
    assert result["achievement_score"] > 49
    # F6 stays centred on F3, not the policy cap.
    low, high = result["achievement_uncertainty_band"]
    assert (low + high) / 2 == pytest.approx(result["achievement_score"], abs=0.01)


def test_missing_core_data_defers_but_non_core_gaps_keep_a_content_based_score():
    missing = _make_scores(3)
    del missing["methodology"]
    result = compute_score(missing)
    assert result["scoring_complete"] is False
    assert result["final_score"] is None
    assert result["achievement_score"] is None
    assert result["grade_band"] == "DEFERRED"
    assert any("methodology" in reason for reason in result["deferral_reasons"])

    invalid = _make_scores(3)
    invalid["clarity"] = {"score": 4.0, "confidence": "high"}
    result = compute_score(invalid)
    assert result["scoring_complete"] is False
    assert result["content_based_estimate"] is True
    assert result["final_score"] == 75.0
    assert result["grade_band"] == "Merit"
    assert result["deferred"] is False
    assert result["missing_criteria"] == ["clarity"]

    communication_failure = _make_scores(4)
    for criterion in ("structure", "clarity", "referencing", "originality", "professionalism"):
        del communication_failure[criterion]
    result = compute_score(communication_failure)
    assert result["content_based_estimate"] is True
    assert result["final_score"] == 100.0
    assert result["grade_band"] == "Distinction"
    assert result["deferred"] is False


def test_low_confidence_does_not_defer_but_explicit_serious_failures_do():
    scores = _make_scores(4)
    scores["technical_accuracy"] = {"score": 4, "confidence": "low"}
    result = compute_score(scores)
    assert result["scoring_complete"] is True
    assert result["deferred"] is False
    assert result["final_score"] == 100.0

    result = run({"scores": _make_scores(4), "serious_failures": ["document integrity review failed"]})
    assert result["deferred"] is True
    assert result["provisional_score"] == 100.0


def test_consensus_deferral_requires_an_explicit_serious_issue_classification():
    routine = compute_score(
        _make_scores(3),
        {"recommendation": "DEFER", "deferral_reason": "Confidence is low"},
    )
    assert routine["deferred"] is False

    serious = compute_score(
        _make_scores(3),
        {"recommendation": "DEFER", "serious_issue": True, "deferral_reason": "Paper is unreadable"},
    )
    assert serious["deferred"] is True
    assert serious["final_score"] is None


def test_holistic_missing_is_unavailable_and_disagreement_does_not_change_score():
    scores = _make_scores(3, holistic_level=4)
    result = compute_score(scores)
    assert result["final_score"] == 75.0
    assert result["holistic_validation"]["requires_moderation"] is True

    del scores["holistic_quality"]
    result = compute_score(scores)
    assert result["scoring_complete"] is True
    assert result["holistic_validation"]["available"] is False


def test_unrounded_policy_score_controls_band_boundaries():
    # Construct 79.5 and 64.5 scores using only valid rubric levels/weights.
    scores = _make_scores(3)
    scores["technical_accuracy"] = {"score": 4, "confidence": "high"}  # 75 + 4.5 = 79.5
    result = compute_score(scores)
    assert result["final_policy_score"] == 79.5
    assert result["grade_band"] == "Merit"

    scores = _make_scores(2)
    for criterion in ("technical_accuracy", "critical_thinking", "evidence_quality", "clarity", "professionalism"):
        scores[criterion] = {"score": 3, "confidence": "high"}
    result = compute_score(scores)
    assert result["final_policy_score"] == 64.5
    assert result["grade_band"] == "Pass"
