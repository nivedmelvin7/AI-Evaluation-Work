"""Stage 4: validated, self-consistent Communication Specialist review."""

from typing import Any, Dict, List

from app.pipeline.reviewer_runner import run_self_consistent_reviewer
from app.prompts.stage4_communication_prompts import COMMUNICATION_SYSTEM, COMMUNICATION_USER_TEMPLATE
from app.rubric import criteria_for_reviewer
from app.services.llm_service import LLMService

COMMUNICATION_CRITERIA = list(criteria_for_reviewer("Communication Specialist"))
REVIEWER_NAME = "Communication Specialist"
XML_ROOT_TAG = "communication_review"


async def run(llm: LLMService, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    return await run_self_consistent_reviewer(
        llm=llm,
        reviewer_name=REVIEWER_NAME,
        criteria=COMMUNICATION_CRITERIA,
        xml_root_tag=XML_ROOT_TAG,
        system_prompt=COMMUNICATION_SYSTEM,
        user_template=COMMUNICATION_USER_TEMPLATE,
        sections=sections,
    )
