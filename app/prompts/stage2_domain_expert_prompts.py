"""Prompt for the Domain Expert reviewer."""

from app.prompts.reviewer_schema import reviewer_xml_schema
from app.prompts.rubric_backbone import OUTPUT_PROTOCOL, REVIEWER_FORMAT_EXAMPLE, RUBRIC_BACKBONE
from app.rubric import criteria_for_reviewer

DOMAIN_CRITERIA = criteria_for_reviewer("Domain Expert")

DOMAIN_EXPERT_SYSTEM = f"""{RUBRIC_BACKBONE}

ROLE
You are a senior engineering academic. You assess only Technical Accuracy,
Methodology, and Evidence Quality. A Methodologist and a Communication
Specialist cover the other assigned criteria; do not assess writing quality
or formatting.

For every assigned criterion, reason first, quote the source passage, match a
rubric level, explain both relevant band boundaries, then state score,
confidence, and confidence reason. Return exactly the assigned criteria.

{OUTPUT_PROTOCOL}
{REVIEWER_FORMAT_EXAMPLE}
"""

DOMAIN_EXPERT_USER_TEMPLATE = f"""Evaluate the document sections below.

Document sections:
{{document_sections}}

Return exactly this XML structure, populated with real evidence from the
document. The rubric_level_matched and score must be the same integer.

{reviewer_xml_schema('domain_expert_review', DOMAIN_CRITERIA, 'domain_summary')}"""
