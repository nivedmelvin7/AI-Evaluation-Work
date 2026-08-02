"""Validated internal assessments used by every scoring stage."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from app.rubric import ALL_CRITERIA, RUBRIC_BY_ID


CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
_WHITESPACE = re.compile(r"\s+")


def normalize_whitespace(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


class CriterionAssessment(BaseModel):
    """An assessment that is valid only after document evidence is checked."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str
    score: int
    confidence: str
    reasoning: str
    evidence: str
    band_justification: str
    confidence_reason: str
    source_reviewer: str
    source_run: int
    evidence_verified: bool = True
    validation_warnings: List[str] = []
    validation_status: str = "valid"
    validation_errors: List[str] = []

    @field_validator("criterion_id")
    @classmethod
    def _known_criterion(cls, value: str) -> str:
        if value not in ALL_CRITERIA:
            raise ValueError("unknown criterion")
        return value

    @field_validator("score", mode="before")
    @classmethod
    def _strict_score(cls, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 4:
            raise ValueError("score must be an integer from 0 to 4")
        return value

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value: Any) -> str:
        if not isinstance(value, str) or value.strip().lower() not in CONFIDENCE_RANK:
            raise ValueError("confidence must be High, Medium, or Low")
        return value.strip().lower()

    @field_validator("reasoning", "evidence", "band_justification", "confidence_reason")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("field must not be empty")
        return value.strip()

    @field_validator("source_reviewer")
    @classmethod
    def _source_reviewer(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("source reviewer is required")
        return value.strip()

    @field_validator("source_run", mode="before")
    @classmethod
    def _source_run(cls, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("source run must be a positive integer")
        return value


@dataclass(frozen=True)
class AssessmentValidation:
    assessment: Optional[CriterionAssessment]
    errors: List[str]
    warnings: List[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return self.assessment is not None and not self.errors


def evidence_in_document(evidence: str, document_text: str) -> bool:
    """Verify evidence using whitespace-normalised exact containment only."""
    normalized_evidence = normalize_whitespace(evidence)
    normalized_document = normalize_whitespace(document_text)
    return bool(normalized_evidence and normalized_document and normalized_evidence in normalized_document)


def validate_assessment(
    payload: Dict[str, Any],
    document_text: str,
    *,
    allow_unverified_evidence: bool = False,
) -> AssessmentValidation:
    """Build an assessment and verify its supporting quotation when possible.

    A well-formed reviewer judgement should not be discarded solely because an
    LLM slightly reformatted a quotation while copying it from a PDF.  Callers
    that need a hard evidence gate can keep the default; the evaluation
    pipeline opts into a warning so it can still rate the submitted content.
    """
    try:
        assessment = CriterionAssessment.model_validate(payload)
    except ValidationError as exc:
        return AssessmentValidation(None, [error["msg"] for error in exc.errors()])

    criterion = RUBRIC_BY_ID[assessment.criterion_id]
    errors: List[str] = []
    warnings: List[str] = []
    if criterion.requires_quotation and not evidence_in_document(assessment.evidence, document_text):
        message = "evidence quotation could not be automatically matched to the submitted document"
        if allow_unverified_evidence:
            warnings.append(message)
            assessment = assessment.model_copy(update={
                "evidence_verified": False,
                "validation_warnings": [*assessment.validation_warnings, message],
            })
        else:
            errors.append(message)
    # A boundary explanation must make clear why an adjacent level is excluded.
    boundary = assessment.band_justification.lower()
    if assessment.score < 4 and not any(token in boundary for token in ("not", "below", "does not", "isn't", "is not")):
        errors.append("band justification does not explain the adjacent level above")
    if assessment.score > 0 and not any(token in boundary for token in ("not", "above", "than", "isn't", "is not")):
        errors.append("band justification does not explain the adjacent level below")
    if errors:
        return AssessmentValidation(None, errors, warnings)
    return AssessmentValidation(assessment, [], warnings)


def assessment_to_dict(assessment: CriterionAssessment | Dict[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe copy while supporting existing dict call sites."""
    if isinstance(assessment, CriterionAssessment):
        return assessment.model_dump()
    return dict(assessment)


def validate_complete_assessments(
    payloads: Iterable[Dict[str, Any]],
    expected_criteria: Iterable[str],
    document_text: str,
    *,
    allow_unverified_evidence: bool = False,
) -> tuple[Dict[str, Dict[str, Any]], List[str]]:
    """Validate exact criterion coverage and return serialisable assessments."""
    expected = tuple(expected_criteria)
    by_id: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    for payload in payloads:
        criterion_id = payload.get("criterion_id", "") if isinstance(payload, dict) else ""
        if criterion_id in by_id:
            errors.append(f"duplicate criterion: {criterion_id}")
            continue
        result = validate_assessment(
            payload,
            document_text,
            allow_unverified_evidence=allow_unverified_evidence,
        )
        if not result.valid:
            errors.extend(f"{criterion_id or 'unknown criterion'}: {error}" for error in result.errors)
            continue
        by_id[criterion_id] = assessment_to_dict(result.assessment)
    missing = set(expected) - set(by_id)
    extras = set(by_id) - set(expected)
    errors.extend(f"missing criterion: {criterion}" for criterion in sorted(missing))
    errors.extend(f"unexpected criterion: {criterion}" for criterion in sorted(extras))
    return by_id, errors
