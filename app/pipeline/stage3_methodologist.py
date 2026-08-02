"""Stage 3: validated, self-consistent Methodologist review."""

from typing import Any, Dict, List

from app.pipeline.reviewer_runner import run_self_consistent_reviewer
from app.prompts.stage3_methodologist_prompts import METHODOLOGIST_SYSTEM, METHODOLOGIST_USER_TEMPLATE
from app.rubric import criteria_for_reviewer
from app.services.llm_service import LLMService

METHODOLOGIST_CRITERIA = list(criteria_for_reviewer("Methodologist"))
REVIEWER_NAME = "Methodologist"
XML_ROOT_TAG = "methodologist_review"


async def run(llm: LLMService, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    return await run_self_consistent_reviewer(
        llm=llm,
        reviewer_name=REVIEWER_NAME,
        criteria=METHODOLOGIST_CRITERIA,
        xml_root_tag=XML_ROOT_TAG,
        system_prompt=METHODOLOGIST_SYSTEM,
        user_template=METHODOLOGIST_USER_TEMPLATE,
        sections=sections,
    )
