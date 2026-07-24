"""Integration and unit tests for the evaluation pipeline."""

import json
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Sample engineering report fixture (≈200 words, exercises all 10 criteria)
# ---------------------------------------------------------------------------

SAMPLE_REPORT = """
Abstract

This paper investigates the thermal efficiency of shell-and-tube heat exchangers
under turbulent flow conditions (Re = 8,000–25,000). We measured heat transfer
coefficients using a custom-built rig calibrated against NIST Standard Reference
Data. The Nusselt number correlation Nu = 0.023 Re^0.8 Pr^0.4 (Dittus-Boelter)
was validated against our experimental data with a maximum deviation of 4.2%.

Introduction

Heat exchangers are ubiquitous in chemical processing and HVAC systems. Despite
extensive prior work (Incropera et al., 2007; Bergman & Lavine, 2011), there is
limited experimental data for fouling-resistant alloys at elevated temperatures.
This study addresses that gap by characterising a titanium-grade 2 heat exchanger.

Methodology

Experiments were conducted in steady-state conditions. Inlet and outlet
temperatures were measured using calibrated T-type thermocouples (±0.2 °C).
Flow rates were monitored with a Coriolis flowmeter. Three replicate runs were
performed at each Reynolds number to assess repeatability. Uncertainty analysis
followed the ASME PTC 19.1 standard.

Results and Discussion

Heat transfer coefficients ranged from 1,850 to 6,200 W/m²K. Fouling resistance
increased linearly with temperature above 80 °C, consistent with carbonate
deposition. These results support our hypothesis that titanium surfaces offer
superior fouling resistance compared to stainless steel (Smith et al., 2019).

Conclusions

The experimental data confirm that titanium-grade 2 heat exchangers exhibit
15–22% lower fouling resistance compared to 316L stainless steel at 90 °C.
Further work should examine longer-duration fouling under industrial conditions.

References

Incropera, F. P. et al. (2007). Fundamentals of Heat and Mass Transfer (6th ed.).
Bergman, T. L. & Lavine, A. S. (2011). Introduction to Heat Transfer (5th ed.).
Smith, J. et al. (2019). Journal of Heat Transfer, 141(3), 031801.
"""


# ---------------------------------------------------------------------------
# XML parser tests
# ---------------------------------------------------------------------------

from app.utils.xml_parser import parse_xml_response, extract_scores_from_review


def test_xml_parser_well_formed():
    raw = """
    <domain_expert_review>
      <criterion id="technical_accuracy">
        <reasoning>Good derivations.</reasoning>
        <score>3</score>
        <confidence>High</confidence>
      </criterion>
    </domain_expert_review>
    """
    root = parse_xml_response(raw, "domain_expert_review")
    assert root is not None
    assert root.tag == "domain_expert_review"


def test_xml_parser_with_markdown_fences():
    raw = """```xml
    <domain_expert_review>
      <criterion id="methodology">
        <reasoning>Sound.</reasoning>
        <score>2</score>
        <confidence>Medium</confidence>
      </criterion>
    </domain_expert_review>
    ```"""
    root = parse_xml_response(raw, "domain_expert_review")
    assert root is not None


def test_xml_parser_malformed_ampersand():
    raw = """<audit>
      <issues>
        <issue id="1">
          <description>Score &amp; confidence mismatch.</description>
        </issue>
      </issues>
      <overall_quality>High</overall_quality>
      <audit_summary>One issue found.</audit_summary>
    </audit>"""
    root = parse_xml_response(raw, "audit")
    assert root is not None


def test_xml_parser_returns_none_on_garbage():
    root = parse_xml_response("This is not XML at all.", "domain_expert_review")
    assert root is None


def test_extract_scores_from_review():
    raw = """<domain_expert_review>
      <criterion id="technical_accuracy">
        <reasoning>Well-reasoned derivations found throughout.</reasoning>
        <score>3</score>
        <confidence>High</confidence>
      </criterion>
      <criterion id="methodology">
        <reasoning>Adequate experimental design.</reasoning>
        <score>2</score>
        <confidence>Medium</confidence>
      </criterion>
    </domain_expert_review>"""
    root = parse_xml_response(raw, "domain_expert_review")
    assert root is not None
    scores = extract_scores_from_review(root, ["technical_accuracy", "methodology"])
    assert scores["technical_accuracy"]["score"] == 3
    assert scores["technical_accuracy"]["confidence"] == "high"
    assert scores["methodology"]["score"] == 2


def test_extract_scores_handles_unchanged_format():
    raw = """<final_scores reviewer="Domain Expert">
      <score criterion="technical_accuracy" value="Unchanged: 3" confidence="High"/>
    </final_scores>"""
    root = parse_xml_response(raw, "final_scores")
    assert root is not None
    # The extract helper also parses criteria from <criterion> elements,
    # but revised_score from final_scores uses attribute format — test raw parse
    import re
    score_el = root.find(".//score[@criterion='technical_accuracy']")
    value_str = score_el.get("value", "2")
    assert "Unchanged" in value_str
    match = re.search(r"\d", value_str)
    assert match is not None
    assert int(match.group()) == 3


# ---------------------------------------------------------------------------
# Stage 8 scoring tests (imported directly to avoid LLM dependency)
# ---------------------------------------------------------------------------

from app.pipeline.stage8_scoring import compute_score, CRITERION_WEIGHTS


def _uniform_scores(level: int, confidence: str = "high") -> dict:
    return {c: {"score": level, "confidence": confidence} for c in CRITERION_WEIGHTS}


def test_full_marks():
    result = compute_score(_uniform_scores(4, "high"))
    assert result["final_score"] >= 95
    assert result["grade_band"] == "Distinction"


def test_gate_caps_at_49():
    scores = _uniform_scores(4, "high")
    scores["technical_accuracy"] = {"score": 1, "confidence": "high"}
    result = compute_score(scores)
    assert result["gate_triggered"] is True
    assert result["final_score"] <= 49


# ---------------------------------------------------------------------------
# API endpoint tests (no LLM called — uses TestClient)
# ---------------------------------------------------------------------------

from main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "backend" in data
    assert "model" in data


def test_evaluate_returns_job_id():
    resp = client.post(
        "/api/v1/evaluate",
        data={"raw_text": SAMPLE_REPORT},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_status_endpoint_queued():
    resp = client.post("/api/v1/evaluate", data={"raw_text": SAMPLE_REPORT})
    job_id = resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/status/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["job_id"] == job_id
    assert data["status"] in ("queued", "running", "complete", "failed")


def test_status_404_unknown_job():
    resp = client.get("/api/v1/status/nonexistent-job-id-xyz")
    assert resp.status_code == 404


def test_result_404_unknown_job():
    resp = client.get("/api/v1/result/nonexistent-job-id-xyz")
    assert resp.status_code == 404


def test_evaluate_rejects_empty_text():
    resp = client.post("/api/v1/evaluate", data={"raw_text": "   "})
    assert resp.status_code == 400


def test_evaluate_requires_input():
    resp = client.post("/api/v1/evaluate", data={})
    assert resp.status_code == 400


def test_sync_endpoint_blocked_without_key():
    """Sync endpoint should require secret key when APP_DEBUG=false."""
    resp = client.post(
        "/api/v1/evaluate/sync",
        data={"raw_text": SAMPLE_REPORT},
    )
    # Should be 403 (wrong/missing key) unless debug mode is on
    from app.config import get_settings
    settings = get_settings()
    if not settings.app_debug:
        assert resp.status_code == 403


def test_docs_available():
    resp = client.get("/docs")
    assert resp.status_code == 200
