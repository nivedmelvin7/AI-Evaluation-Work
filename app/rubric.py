"""Authoritative rubric policy shared by prompts, pipeline, and scoring.

Keeping this data in one place prevents a reviewer prompt, consensus rule, or
deterministic score calculation from quietly drifting away from the policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, Mapping, Tuple


REVIEWERS: Tuple[str, ...] = (
    "Domain Expert",
    "Methodologist",
    "Communication Specialist",
)


@dataclass(frozen=True)
class RubricCriterion:
    criterion_id: str
    display_name: str
    weight: Decimal | None
    weighted: bool
    critical: bool
    reviewer_coverage: Tuple[str, ...]
    descriptors: Mapping[int, str]
    evidence_requirement: str
    requires_quotation: bool = True

    @property
    def validation_only(self) -> bool:
        return not self.weighted


_LEVELS: Dict[str, Dict[int, str]] = {
    "technical_accuracy": {
        4: "All technical content is correct, including equations, derivations, and quantitative claims.",
        3: "Minor imprecisions do not affect the overall validity.",
        2: "Some errors are present but the central argument remains valid.",
        1: "Significant errors undermine validity.",
        0: "Technical content is pervasively incorrect or fundamentally invalid.",
    },
    "methodology": {
        4: "Method is appropriate, justified, reproducible, and acknowledges limitations.",
        3: "Method is sound with minor gaps in justification.",
        2: "Method is present but some choices are unexplained.",
        1: "Method is poorly described or largely inappropriate.",
        0: "No meaningful methodology is described.",
    },
    "critical_thinking": {
        4: "Deep critical analysis evaluates alternatives and limitations.",
        3: "Good critical engagement with occasional description.",
        2: "Some analysis is present but is largely descriptive.",
        1: "Minimal critical thought; mostly assertions.",
        0: "No critical thinking is evident.",
    },
    "evidence_quality": {
        4: "Claims are fully supported and data are correctly interpreted.",
        3: "Evidence is used well with minor gaps.",
        2: "Some claims are unsupported or evidence is inconsistently applied.",
        1: "Major claims are unsupported or evidence is misinterpreted.",
        0: "No meaningful evidence supports the claims.",
    },
    "structure": {
        4: "Structure is logical and coherent, with all important sections present.",
        3: "Structure is good with minor gaps or transitions that are unclear.",
        2: "Basic structure is present but some sections or links are weak.",
        1: "Structure is poor, with major sections absent or misplaced.",
        0: "There is no discernible structure.",
    },
    "clarity": {
        4: "Writing is clear, precise, and unambiguous in an appropriate register.",
        3: "Writing is clear with minor ambiguities.",
        2: "Writing is understandable but has notable clarity issues.",
        1: "Frequent clarity problems hinder understanding.",
        0: "The work is largely incomprehensible.",
    },
    "referencing": {
        4: "Claims are attributed, style is consistent, and references are reliable.",
        3: "Referencing is good with minor inconsistencies.",
        2: "Referencing is present but incomplete or inconsistent.",
        1: "Referencing is poor and many claims are unattributed.",
        0: "Referencing is absent or completely unreliable.",
    },
    "originality": {
        4: "There is a clear original contribution and independent thinking.",
        3: "There is some originality and genuine synthesis.",
        2: "Originality is limited and much content reproduces known material.",
        1: "There is minimal independent thought and the work is heavily derivative.",
        0: "The work is pure reproduction with no original contribution.",
    },
    "professionalism": {
        4: "Presentation is professional with no material spelling, grammar, or formatting errors.",
        3: "Presentation is professional with minor presentational issues.",
        2: "Some problems exist but presentation is generally acceptable.",
        1: "Notable presentation failures affect readability.",
        0: "Presentation is unprofessional throughout.",
    },
    "holistic_quality": {
        4: "Overall Distinction quality.",
        3: "Overall Merit quality.",
        2: "Overall Pass quality.",
        1: "Overall borderline-fail quality.",
        0: "Overall clear-fail quality.",
    },
}


RUBRIC: Tuple[RubricCriterion, ...] = (
    RubricCriterion("technical_accuracy", "Technical accuracy", Decimal("0.18"), True, True, ("Domain Expert",), _LEVELS["technical_accuracy"], "Quote the technical claim, equation, derivation, result, or relevant absence being assessed."),
    RubricCriterion("methodology", "Methodology", Decimal("0.15"), True, True, ("Domain Expert", "Methodologist"), _LEVELS["methodology"], "Quote the method, design choice, reproducibility detail, limitation, or relevant absence being assessed."),
    RubricCriterion("critical_thinking", "Critical thinking", Decimal("0.14"), True, False, ("Methodologist",), _LEVELS["critical_thinking"], "Quote analysis, alternatives, limitations, or conclusions that support the judgement."),
    RubricCriterion("evidence_quality", "Evidence quality", Decimal("0.12"), True, False, ("Domain Expert", "Methodologist"), _LEVELS["evidence_quality"], "Quote the claim and its data, source, or other evidential support being assessed."),
    RubricCriterion("structure", "Structure and organisation", Decimal("0.12"), True, False, ("Communication Specialist",), _LEVELS["structure"], "Quote headings, transitions, or representative organisation evidence."),
    RubricCriterion("clarity", "Clarity and communication", Decimal("0.10"), True, False, ("Communication Specialist",), _LEVELS["clarity"], "Quote representative language that demonstrates the clarity judgement."),
    RubricCriterion("referencing", "Referencing integrity", Decimal("0.08"), True, False, ("Communication Specialist",), _LEVELS["referencing"], "Quote citations, claims, or reference-list entries that demonstrate the judgement."),
    RubricCriterion("originality", "Originality", Decimal("0.07"), True, False, ("Communication Specialist",), _LEVELS["originality"], "Quote the claimed contribution, synthesis, or reproduced material being assessed."),
    RubricCriterion("professionalism", "Professionalism", Decimal("0.04"), True, False, ("Communication Specialist",), _LEVELS["professionalism"], "Quote representative presentational content that demonstrates the judgement."),
    RubricCriterion("holistic_quality", "Holistic quality", None, False, False, ("Communication Specialist",), _LEVELS["holistic_quality"], "Quote representative document evidence supporting the overall-quality judgement."),
)


def validate_rubric(rubric: Iterable[RubricCriterion] = RUBRIC) -> None:
    """Fail deterministically on invalid policy data at import/start-up time."""
    criteria = tuple(rubric)
    ids = [criterion.criterion_id for criterion in criteria]
    if len(ids) != len(set(ids)):
        raise ValueError("Rubric criterion IDs must be unique")
    weighted = [criterion for criterion in criteria if criterion.weighted]
    if any(criterion.weight is None for criterion in weighted):
        raise ValueError("Weighted criteria must have a weight")
    if sum((criterion.weight or Decimal("0")) for criterion in weighted) != Decimal("1.00"):
        raise ValueError("Weighted rubric criteria must total exactly 1.0")
    holistic = next((criterion for criterion in criteria if criterion.criterion_id == "holistic_quality"), None)
    if holistic is None or holistic.weighted or holistic.weight is not None:
        raise ValueError("Holistic quality must be validation-only and excluded from the weighted total")
    if not {criterion.criterion_id for criterion in criteria if criterion.critical}.issuperset({"technical_accuracy", "methodology"}):
        raise ValueError("Required critical criteria are missing")
    for criterion in criteria:
        if set(criterion.reviewer_coverage) - set(REVIEWERS):
            raise ValueError(f"Unknown reviewer in coverage for {criterion.criterion_id}")
        if set(criterion.descriptors) != {0, 1, 2, 3, 4}:
            raise ValueError(f"Criterion {criterion.criterion_id} must define levels 0 through 4")


validate_rubric()

RUBRIC_BY_ID: Dict[str, RubricCriterion] = {criterion.criterion_id: criterion for criterion in RUBRIC}
ALL_CRITERIA: Tuple[str, ...] = tuple(RUBRIC_BY_ID)
WEIGHTED_CRITERIA: Tuple[str, ...] = tuple(criterion.criterion_id for criterion in RUBRIC if criterion.weighted)
CRITICAL_CRITERIA: Tuple[str, ...] = tuple(criterion.criterion_id for criterion in RUBRIC if criterion.critical)
CRITERION_WEIGHTS: Dict[str, float] = {
    criterion.criterion_id: float(criterion.weight)
    for criterion in RUBRIC
    if criterion.weighted and criterion.weight is not None
}


def criteria_for_reviewer(reviewer_name: str) -> Tuple[str, ...]:
    if reviewer_name not in REVIEWERS:
        raise ValueError(f"Unknown reviewer: {reviewer_name}")
    return tuple(
        criterion.criterion_id
        for criterion in RUBRIC
        if reviewer_name in criterion.reviewer_coverage
    )


def render_rubric_for_prompt() -> str:
    """Render the prompt rubric directly from the authoritative policy."""
    blocks = []
    for index, criterion in enumerate(RUBRIC, start=1):
        header = (
            f"CRITERION {index}: {criterion.display_name.upper()} | Weight: {int(criterion.weight * 100)}%"
            if criterion.weighted and criterion.weight is not None
            else f"CRITERION {index}: {criterion.display_name.upper()} | Validation only (not in weighted total)"
        )
        levels = "\n".join(f"{level} - {criterion.descriptors[level]}" for level in range(4, -1, -1))
        blocks.append(f"{header}\n{levels}\nEvidence requirement: {criterion.evidence_requirement}")
    return "\n\n".join(blocks)
