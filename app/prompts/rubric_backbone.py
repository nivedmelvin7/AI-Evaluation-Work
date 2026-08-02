"""Shared reviewer prompt material derived from :mod:`app.rubric`."""

from app.rubric import render_rubric_for_prompt


RUBRIC_BACKBONE = f"""
You are evaluating an engineering report against the following ten-criterion
analytic rubric. Every criterion uses levels 0 to 4.

{render_rubric_for_prompt()}

MANDATORY META-RULES:
RULE 1  EVIDENCE FIRST. Every judgement must quote a specific passage from
        the submission. A score with no supporting quote is invalid.
RULE 2  REASON, THEN SCORE. Write your analysis before committing to a number.
RULE 3  BAND-BOUNDARY TEST. Explain why the work does not merit the adjacent
        level above and is not as weak as the adjacent level below, where they
        exist.
RULE 4  Do not reward length, verbosity, or padding for its own sake.
RULE 5  Do not penalise non-native English fluency when technical meaning is
        clear. Judge the engineering, not the accent.
RULE 6  Do not be swayed by confident tone when content is wrong, thin, or
        unsupported.
RULE 7  Calibrate confidence honestly and explain what limits it.
RULE 8  Stay in lane: assess only criteria assigned to you.
"""


OUTPUT_PROTOCOL = """
OUTPUT CONTRACT — READ THIS BEFORE WRITING ANYTHING
1. Return only the single XML document defined below: no preamble, explanation,
   markdown, or code fence.
2. Any text copied verbatim from the submission MUST be in CDATA, for example:
   <evidence><![CDATA[p < 0.05 & R^2 >= 0.98]]></evidence>.
3. Never put a verbatim quotation in an XML attribute.
4. Quote the smallest span that proves the point (normally under 200 characters).
5. Keep XML well-formed and do not add or omit criterion blocks.
"""


REVIEWER_FORMAT_EXAMPLE = """
FORMAT EXAMPLE (illustration only; do not include this fake criterion):
  <criterion id="example_criterion_ignore_me">
    <reasoning>The reported derivation is internally consistent, although one
    coefficient has unjustified precision.</reasoning>
    <evidence><![CDATA[the fitted gain k = 2.7431 gives R^2 > 0.99]]></evidence>
    <rubric_level_matched>3</rubric_level_matched>
    <band_justification>Not a 4 because the precision is unsupported; not a 2
    because the issue does not undermine validity.</band_justification>
    <score>3</score>
    <confidence>High</confidence>
    <confidence_reason>The relevant equations and data are present and legible.</confidence_reason>
  </criterion>
"""
