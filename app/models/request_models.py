from pydantic import BaseModel
from typing import Optional


class TextEvaluationRequest(BaseModel):
    raw_text: str
    job_id: Optional[str] = None


class EvaluationStatusResponse(BaseModel):
    job_id: str
    status: str
    stage: str
    progress: int
    error: Optional[str] = None
