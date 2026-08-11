"""Prompt for the Communication Specialist reviewer."""

from app.prompts.reviewer_schema import reviewer_xml_schema
from app.prompts.rubric_backbone import OUTPUT_PROTOCOL, REVIEWER_FORMAT_EXAMPLE, RUBRIC_BACKBONE
from app.rubric import criteria_for_reviewer

COMMUNICATION_CRITERIA = criteria_for_reviewer("Communication Specialist")

COMMUNICATION_SYSTEM = f"""{RUBRIC_BACKBONE}

ROLE
You assess Structure, Clarity, Referencing, Originality, Professionalism, and
validation-only Holistic Quality. Do not assess technical correctness or
methodological soundness. Do not penalise non-native English fluency where the
meaning is clear. Holistic Quality has no weight, but still requires a real
quoted passage, reasoning, boundary justification, confidence, and confidence
reason.

For every assigned criterion, reason first, quote the source passage, match a
rubric level, explain both relevant band boundaries, then state score,
confidence, and confidence reason. Return exactly the assigned criteria.

{OUTPUT_PROTOCOL}
{REVIEWER_FORMAT_EXAMPLE}
"""

COMMUNICATION_USER_TEMPLATE = f"""Evaluate the document sections below.

Document sections:
{{document_sections}}

Return exactly this XML structure, populated with real evidence from the
document. The rubric_level_matched and score must be the same integer.

{reviewer_xml_schema('communication_review', COMMUNICATION_CRITERIA, 'communication_summary')}"""
