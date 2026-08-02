"""XML schema fragments used by all specialist reviewer prompts."""

from __future__ import annotations

from typing import Iterable


def reviewer_xml_schema(root_tag: str, criteria: Iterable[str], summary_tag: str) -> str:
    blocks = []
    for criterion in criteria:
        blocks.append(f'''  <criterion id="{criterion}">
    <reasoning>Reasoning before the score.</reasoning>
    <evidence><![CDATA[exact verbatim quote from the document]]></evidence>
    <rubric_level_matched>0|1|2|3|4</rubric_level_matched>
    <band_justification>Why this is not the adjacent level above and not the adjacent level below where applicable.</band_justification>
    <score>0|1|2|3|4</score>
    <confidence>High|Medium|Low</confidence>
    <confidence_reason>Why this confidence level is warranted.</confidence_reason>
  </criterion>''')
    return "\n".join([
        f"<{root_tag}>",
        *blocks,
        f"  <{summary_tag}>Brief summary.</{summary_tag}>",
        f"</{root_tag}>",
    ])
