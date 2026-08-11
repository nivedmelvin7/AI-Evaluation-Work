"""Validated assessment, self-consistency, and mocked pipeline-flow tests."""

from pathlib import Path

import pytest

from app.models.assessment import validate_assessment
from app.pipeline import compute_median_scores
from app.pipeline import stage2_domain_expert, stage3_methodologist, stage4_communication
from app.pipeline import stage5_self_critique, stage6_reflection, stage7_consensus, stage8_scoring
from app.prompts.stage2_domain_expert_prompts import DOMAIN_EXPERT_SYSTEM
from app.prompts.stage3_methodologist_prompts import METHODOLOGIST_SYSTEM
from app.rubric import CRITICAL_CRITERIA, criteria_for_reviewer
from app.utils.xml_parser import parse_review_assessments, parse_xml_response


DOCUMENT = "This evidence passage is present in the submitted engineering document."
SECTIONS = [{"section_name": "Report", "section_type": "BODY", "status": "PRESENT", "content": DOCUMENT}]


def assessment(criterion: str, score: int = 3, confidence: str = "high", run: int = 1) -> dict:
    return {
        "criterion_id": criterion,
        "score": score,
        "confidence": confidence,
        "reasoning": f"The document supports a level {score} judgement for {criterion}.",
        "evidence": "This evidence passage is present",
        "band_justification": "Not the adjacent level above because the evidence is limited; not the adjacent level below because the required feature is present.",
        "confidence_reason": "The relevant passage is explicit and legible.",
        "source_reviewer": "Test Reviewer",
        "source_run": run,
    }


def reviewer_xml(root: str, criteria: tuple[str, ...] | list[str], score: int = 3) -> str:
    blocks = []
    for criterion in criteria:
        blocks.append(f'''<criterion id="{criterion}">
<reasoning>The document supports a level {score} judgement for {criterion}.</reasoning>
<evidence><![CDATA[This evidence passage is present]]></evidence>
<rubric_level_matched>{score}</rubric_level_matched>
<band_justification>Not the adjacent level above because the evidence is limited; not the adjacent level below because the required feature is present.</band_justification>
<score>{score}</score><confidence>High</confidence>
<confidence_reason>The relevant passage is explicit and legible.</confidence_reason>
</criterion>''')
    return f"<{root}>" + "".join(blocks) + f"</{root}>"


def audit_xml(criteria: tuple[str, ...] | list[str]) -> str:
    issues = "".join(
        f"<issue><type>NONE</type><criterion_affected>{criterion}</criterion_affected><description>No issue found.</description><recommended_correction>None.</recommended_correction></issue>"
        for criterion in criteria
    )
    return f"<audit><issues>{issues}</issues><overall_quality>High</overall_quality><audit_summary>All criteria checked.</audit_summary></audit>"


class FakeLLM:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.prompts: list[str] = []

    async def complete_with_retry(self, *, system_prompt, user_prompt, **_kwargs):
        self.prompts.append(user_prompt)
        if not self.responses:
            raise AssertionError("Unexpected LLM call")
        return self.responses.pop(0)


def completed_reviewer(reviewer: str, criteria: tuple[str, ...]) -> dict:
    return {
        "reviewer_name": reviewer,
        "complete": True,
        "final_scores": {criterion: validate_assessment(assessment(criterion), DOCUMENT).assessment.model_dump() for criterion in criteria},
        "integrity_flags": [], "validation_errors": [],
    }


def test_assessment_validation_rejects_coercion_and_ungrounded_evidence():
    for invalid_score in (True, 3.0, "3", -1, 5):
        payload = assessment("technical_accuracy")
        payload["score"] = invalid_score
        assert not validate_assessment(payload, DOCUMENT).valid
    payload = assessment("technical_accuracy")
    payload["evidence"] = "invented quotation"
    assert not validate_assessment(payload, DOCUMENT).valid
    payload = assessment("technical_accuracy")
    payload["evidence"] = ""
    assert not validate_assessment(payload, DOCUMENT).valid


def test_parser_keeps_a_well_formed_score_when_pdf_quote_matching_is_imperfect():
    xml = reviewer_xml("domain_expert_review", ["technical_accuracy"])
    xml = xml.replace("This evidence passage is present", "This passage was reformatted by PDF extraction")
    root = parse_xml_response(xml, "domain_expert_review")
    scores, errors = parse_review_assessments(
        root, ["technical_accuracy"], DOCUMENT, "Domain Expert", 1
    )
    assert errors == []
    assert scores["technical_accuracy"]["evidence_verified"] is False
    assert scores["technical_accuracy"]["validation_warnings"]


def test_parser_flags_missing_extra_duplicate_and_invalid_fields():
    xml = reviewer_xml("domain_expert_review", ["technical_accuracy"], 5)
    root = parse_xml_response(xml, "domain_expert_review")
    scores, errors = parse_review_assessments(root, ["technical_accuracy", "methodology"], DOCUMENT, "Domain Expert", 1)
    assert scores == {}
    assert any("methodology" in error for error in errors)
    assert any("score" in error.lower() for error in errors)


def test_median_keeps_score_evidence_reasoning_and_confidence_aligned():
    runs = []
    for run, (score, confidence, marker) in enumerate([(2, "low", "first"), (3, "medium", "second"), (3, "high", "third")], start=1):
        item = assessment("technical_accuracy", score, confidence, run)
        item["reasoning"] = marker
        item["evidence"] = f"This evidence passage is present {marker}"
        # Make every quote verifiable for this direct aggregation test.
        runs.append({"technical_accuracy": item})
    result = compute_median_scores(runs, ["technical_accuracy"])["technical_accuracy"]
    assert result["score"] == 3
    assert result["confidence"] == "medium"  # score range 1 caps High at Medium
    assert result["reasoning"] == "third"
    assert result["evidence"].endswith("third")
    assert result["source_run"] == 3
    assert result["score_range"] == 1


def test_prompts_and_coverage_are_centralised_and_truthful():
    assert "OUTPUT CONTRACT" in DOMAIN_EXPERT_SYSTEM
    assert "FORMAT EXAMPLE" in DOMAIN_EXPERT_SYSTEM
    assert "technical_accuracy" not in criteria_for_reviewer("Methodologist")
    assert "technical accuracy" not in METHODOLOGIST_SYSTEM.lower().split("role", 1)[-1].split("do not assess", 1)[0]
    assert set(CRITICAL_CRITERIA) == {"technical_accuracy", "methodology"}


@pytest.mark.asyncio
async def test_audit_receives_structured_median_evidence_and_reflection_rejects_partial_output():
    original = {
        "reviewer_name": "Domain Expert", "complete": True,
        "scores": {criterion: validate_assessment(assessment(criterion), DOCUMENT).assessment.model_dump() for criterion in criteria_for_reviewer("Domain Expert")},
    }
    llm = FakeLLM([audit_xml(criteria_for_reviewer("Domain Expert"))])
    audit = await stage5_self_critique.run(llm, "Domain Expert", original)
    assert audit["complete"] is True
    assert "evidence" in llm.prompts[0] and "reasoning" in llm.prompts[0]

    partial = reviewer_xml("final_scores", ["technical_accuracy"])
    reflection = await stage6_reflection.run(FakeLLM([partial]), "Domain Expert", original, audit, SECTIONS)
    assert reflection["complete"] is False
    assert reflection["provisional"] is True
    assert set(reflection["final_scores"]) == set(criteria_for_reviewer("Domain Expert"))


@pytest.mark.asyncio
async def test_consensus_prompt_receives_evidence_and_preserves_single_reviewer_assessments():
    de = completed_reviewer("Domain Expert", criteria_for_reviewer("Domain Expert"))
    meth = completed_reviewer("Methodologist", criteria_for_reviewer("Methodologist"))
    comm = completed_reviewer("Communication Specialist", criteria_for_reviewer("Communication Specialist"))
    consensus_xml = reviewer_xml("consensus", ["methodology", "evidence_quality"])
    llm = FakeLLM([consensus_xml])
    result = await stage7_consensus.run(llm, de, meth, comm, DOCUMENT)
    assert result["complete"] is True
    assert "evidence" in llm.prompts[0] and "band_justification" in llm.prompts[0]
    assert result["scores"]["technical_accuracy"]["source_reviewer"] == "Test Reviewer"
    assert result["scores"]["methodology"]["source_reviewer"] == "Consensus"


@pytest.mark.asyncio
async def test_mocked_end_to_end_assessment_flow_is_publishable_only_when_complete():
    domain_criteria = tuple(criteria_for_reviewer("Domain Expert"))
    method_criteria = tuple(criteria_for_reviewer("Methodologist"))
    communication_criteria = tuple(criteria_for_reviewer("Communication Specialist"))
    responses = (
        [reviewer_xml("domain_expert_review", domain_criteria)] * 3
        + [reviewer_xml("methodologist_review", method_criteria)] * 3
        + [reviewer_xml("communication_review", communication_criteria)] * 3
        + [audit_xml(domain_criteria), audit_xml(method_criteria), audit_xml(communication_criteria)]
        + [reviewer_xml("final_scores", domain_criteria), reviewer_xml("final_scores", method_criteria), reviewer_xml("final_scores", communication_criteria)]
        + [reviewer_xml("consensus", ["methodology", "evidence_quality"])]
    )
    llm = FakeLLM(responses)
    de = await stage2_domain_expert.run(llm, SECTIONS)
    meth = await stage3_methodologist.run(llm, SECTIONS)
    comm = await stage4_communication.run(llm, SECTIONS)
    assert de["complete"] and meth["complete"] and comm["complete"]
    de_audit = await stage5_self_critique.run(llm, "Domain Expert", de)
    meth_audit = await stage5_self_critique.run(llm, "Methodologist", meth)
    comm_audit = await stage5_self_critique.run(llm, "Communication Specialist", comm)
    de_final = await stage6_reflection.run(llm, "Domain Expert", de, de_audit, SECTIONS)
    meth_final = await stage6_reflection.run(llm, "Methodologist", meth, meth_audit, SECTIONS)
    comm_final = await stage6_reflection.run(llm, "Communication Specialist", comm, comm_audit, SECTIONS)
    consensus = await stage7_consensus.run(llm, de_final, meth_final, comm_final, DOCUMENT)
    result = stage8_scoring.run(consensus)
    assert result["scoring_complete"] is True
    assert result["deferred"] is False
    assert result["final_score"] == 75.0


def test_frontend_and_exports_have_null_and_provisional_semantics():
    root = Path(__file__).parents[1]
    gauge = (root / "frontend/src/components/ScoreGauge.jsx").read_text(encoding="utf-8")
    workspace = (root / "frontend/src/pages/ResultWorkspace.jsx").read_text(encoding="utf-8")
    assert "Not scored" in gauge
    assert "provisional_score" in gauge
    assert "provisional_score" in workspace and "Scoring complete" in workspace
