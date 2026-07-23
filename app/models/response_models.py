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


class ScoringResult(BaseModel):
    criterion_breakdown: Dict[str, CriterionScore]
    weighted_sum_A: float
    baseline_score: float
    achievement_score: float
    aggregate_uncertainty_U: float
    uncertainty_band: List[float]
    gate_triggered: bool
    gate_reason: Optional[str]
    deferred: bool
    deferral_reason: Optional[str]
    holistic_validation: Dict[str, Any]
    final_score: int
    grade_band: str


class EvaluationResult(BaseModel):
    job_id: str
    status: str
    scoring: Dict[str, Any]
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
