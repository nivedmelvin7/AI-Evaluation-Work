"""Stage 2: validated, self-consistent Domain Expert review."""

from typing import Any, Dict, List

from app.pipeline.reviewer_runner import run_self_consistent_reviewer
from app.prompts.stage2_domain_expert_prompts import DOMAIN_EXPERT_SYSTEM, DOMAIN_EXPERT_USER_TEMPLATE
from app.rubric import criteria_for_reviewer
from app.services.llm_service import LLMService

DOMAIN_CRITERIA = list(criteria_for_reviewer("Domain Expert"))
REVIEWER_NAME = "Domain Expert"
XML_ROOT_TAG = "domain_expert_review"


async def run(llm: LLMService, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    return await run_self_consistent_reviewer(
        llm=llm,
        reviewer_name=REVIEWER_NAME,
        criteria=DOMAIN_CRITERIA,
        xml_root_tag=XML_ROOT_TAG,
        system_prompt=DOMAIN_EXPERT_SYSTEM,
        user_template=DOMAIN_EXPERT_USER_TEMPLATE,
        sections=sections,
    )
