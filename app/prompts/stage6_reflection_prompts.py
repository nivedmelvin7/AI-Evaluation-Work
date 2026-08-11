"""Prompt for the structured reflection stage."""

from app.prompts.rubric_backbone import OUTPUT_PROTOCOL, REVIEWER_FORMAT_EXAMPLE

REFLECTION_SYSTEM = f"""You are the reviewer revisiting a structured assessment after audit.
For every assigned criterion, return a complete assessment even when its score
is unchanged: explicitly preserve its reasoning, evidence, rubric-level match,
band-boundary justification, confidence, and confidence reason. Do not use
"Unchanged" placeholders because the parser needs the complete record.

{OUTPUT_PROTOCOL}
{REVIEWER_FORMAT_EXAMPLE}
"""

REFLECTION_USER_TEMPLATE = """Reviewer: {reviewer_name}

Authoritative median assessment:
{original_output}

Audit findings:
{audit_output}

Document sections:
{document_sections}

Return one <final_scores> XML root. It must contain exactly one <criterion>
block for every criterion in the authoritative assessment and each block must
contain reasoning, CDATA evidence, rubric_level_matched, band_justification,
score, confidence, and confidence_reason. The rubric_level_matched and score
must be equal. Return no text outside XML.

<final_scores reviewer="{reviewer_name}">
  <criterion id="criterion_id">
    <reasoning>Complete reasoning.</reasoning>
    <evidence><![CDATA[exact evidence from the document]]></evidence>
    <rubric_level_matched>0|1|2|3|4</rubric_level_matched>
    <band_justification>Why not the adjacent level above/below where applicable.</band_justification>
    <score>0|1|2|3|4</score>
    <confidence>High|Medium|Low</confidence>
    <confidence_reason>Reason for confidence.</confidence_reason>
  </criterion>
</final_scores>"""
