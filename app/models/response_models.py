from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class CriterionScore(BaseModel):
    level: int
    s_i: float
    weight: float
    contribution: float
    confidence: str
    u_i: float
    uncertainty_contribution: float
    confidence_risk: Optional[float] = None
    evidence: Optional[str] = None
    reasoning: Optional[str] = None
    band_justification: Optional[str] = None
    consensus_rationale: Optional[str] = None


class ScoringResult(BaseModel):
    criterion_breakdown: Dict[str, CriterionScore]
    weighted_sum_A: Optional[float]
    baseline_score: Optional[float]
    achievement_score: Optional[float]
    final_policy_score: Optional[float] = None
    aggregate_uncertainty_U: Optional[float]
    achievement_uncertainty_band: Optional[List[float]] = None
    uncertainty_band: Optional[List[float]] = None
    gate_triggered: bool
    gate_reason: Optional[str]
    scoring_complete: bool
    content_based_estimate: bool = False
    assessment_coverage_weight: Optional[float] = None
    missing_criteria: List[str] = []
    deferred: bool
    deferral_reasons: List[str] = []
    deferral_reason: Optional[str] = None
    holistic_validation: Dict[str, Any]
    final_score: Optional[float]
    provisional_score: Optional[float] = None
    provisional_grade_band: Optional[str] = None
    grade_band: str


class EvaluationResult(BaseModel):
    job_id: str
    status: str
    scoring: ScoringResult
    feedback: Dict[str, Any]
    verification: Dict[str, Any]
    consensus: Dict[str, Any]
    pipeline_metadata: Dict[str, Any]


class PipelineStatus(BaseModel):
    job_id: str
    status: str
    stage: str
    progress: int
    error: Optional[str] = None
