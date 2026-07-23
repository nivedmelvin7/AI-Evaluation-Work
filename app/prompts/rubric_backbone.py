# ---------------------------------------------------------------------------
# Shared prompt components used across the evaluation pipeline.
#
#   RUBRIC_BACKBONE   - the ten-criterion analytic rubric + meta-rules
#   OUTPUT_PROTOCOL   - the machine-parseable output contract (CDATA safety),
#                       reused by every stage that returns XML
#   REVIEWER_FORMAT_EXAMPLE - one worked criterion block that locks the format
# ---------------------------------------------------------------------------

RUBRIC_BACKBONE = """
You are evaluating an engineering report against the following
ten-criterion analytic rubric. Each criterion is scored 0 to 4.

CRITERION 1: TECHNICAL ACCURACY | Weight: 18%
4 - Excellent: All technical content correct. Equations, derivations,
    and quantitative claims accurate and well-justified. No errors.
3 - Good: Minor imprecisions that do not affect overall validity.
2 - Adequate: Some errors present but central argument remains valid.
1 - Weak: Significant errors that undermine validity.
0 - Inadequate: Pervasive errors. Content fundamentally incorrect.

CRITERION 2: STRUCTURE AND ORGANISATION | Weight: 12%
4 - Excellent: Logical, coherent structure. All sections present.
3 - Good: Good structure with minor gaps or unclear transitions.
2 - Adequate: Basic structure present. Some sections missing.
1 - Weak: Poor structure. Major sections absent or misplaced.
0 - Inadequate: No discernible structure.

CRITERION 3: METHODOLOGY | Weight: 15%
4 - Excellent: Appropriate, justified, reproducible. Limitations
    acknowledged. Design choices explained.
3 - Good: Sound methodology with minor gaps in justification.
2 - Adequate: Methodology present but some choices unexplained.
1 - Weak: Poorly described or largely inappropriate.
0 - Inadequate: No methodology described.

CRITERION 4: EVIDENCE QUALITY | Weight: 12%
4 - Excellent: Claims fully supported. Data correctly interpreted.
3 - Good: Good evidence use with minor gaps.
2 - Adequate: Some claims unsupported. Evidence not always applied.
1 - Weak: Major claims unsupported. Evidence misinterpreted.
0 - Inadequate: No meaningful evidence.

CRITERION 5: CRITICAL THINKING | Weight: 14%
4 - Excellent: Deep critical analysis. Alternatives evaluated.
    Conclusions justified. Honest treatment of limitations.
3 - Good: Good critical engagement with occasional description.
2 - Adequate: Some analysis present but largely descriptive.
1 - Weak: Minimal critical thought. Mostly assertions.
0 - Inadequate: No critical thinking evident.

CRITERION 6: CLARITY AND COMMUNICATION | Weight: 10%
4 - Excellent: Clear, precise, unambiguous. Appropriate register.
3 - Good: Clear with minor ambiguities.
2 - Adequate: Understandable but with notable clarity issues.
1 - Weak: Frequent problems that hinder understanding.
0 - Inadequate: Largely incomprehensible.

CRITERION 7: REFERENCING INTEGRITY | Weight: 8%
4 - Excellent: All claims attributed. Consistent style. No fabrications.
3 - Good: Good referencing with minor inconsistencies.
2 - Adequate: Present but inconsistent or incomplete.
1 - Weak: Poor referencing. Many claims unattributed.
0 - Inadequate: No referencing or completely unreliable.

CRITERION 8: ORIGINALITY | Weight: 7%
4 - Excellent: Clear original contribution. Independent thinking.
3 - Good: Some originality. Synthesises rather than reproduces.
2 - Adequate: Limited originality. Largely reproduces existing knowledge.
1 - Weak: Minimal independent thought. Heavily derivative.
0 - Inadequate: No originality. Pure reproduction.

CRITERION 9: PROFESSIONALISM | Weight: 4%
4 - Excellent: Professional formatting. No spelling or grammar errors.
3 - Good: Professional with minor presentational issues.
2 - Adequate: Some problems but generally acceptable.
1 - Weak: Notable failures affecting readability.
0 - Inadequate: Unprofessional throughout.

CRITERION 10: HOLISTIC QUALITY | Validation only (not in weighted total)
4 - Distinction quality
3 - Merit quality
2 - Pass quality
1 - Borderline fail
0 - Clear fail

MANDATORY META-RULES:
RULE 1  EVIDENCE FIRST. Every judgement MUST be anchored to a specific
        quoted passage from the submission. Quote before you judge, never
        after. A score with no supporting quote is invalid.
RULE 2  REASON, THEN SCORE. Write your full analysis before you commit to
        a number. Never state the score first and rationalise afterwards.
RULE 3  BAND-BOUNDARY TEST. After choosing a level, justify it against its
        neighbours: say explicitly why the work does not merit the level
        above and is not as weak as the level below. This is the single
        most important step for a defensible, non-arbitrary score.
RULE 4  DO NOT reward length, verbosity, or padding for its own sake.
RULE 5  DO NOT penalise non-native English fluency when the technical
        meaning is clear. Judge the engineering, not the accent.
RULE 6  DO NOT be swayed by confident or authoritative tone when the
        underlying content is wrong, thin, or unsupported.
RULE 7  CALIBRATE CONFIDENCE honestly. State High / Medium / Low for every
        score and say what would raise or lower it (e.g. missing sections,
        ambiguous data, content outside your certainty).
RULE 8  STAY IN LANE. Assess only the criteria assigned to you. Do not
        silently re-grade a criterion that belongs to another reviewer.
"""


# ---------------------------------------------------------------------------
# OUTPUT CONTRACT — the fix for the class of failure where verbatim
# engineering text (containing <, >, <=, >=, &, %, ") breaks XML parsing.
# CDATA lets the model copy source text verbatim WITHOUT escaping anything.
# ---------------------------------------------------------------------------

OUTPUT_PROTOCOL = """
OUTPUT CONTRACT — READ THIS BEFORE WRITING ANYTHING
1. Return ONLY the single XML document defined below. No preamble, no
   explanation, no markdown, and no ``` code fences before or after it.
2. Any text you copy VERBATIM from the submission — quotations, equations,
   variable names, inequalities, units — MUST be wrapped in a CDATA section:
       <evidence><![CDATA[ the exact text, e.g. p < 0.05 & R^2 >= 0.98 ]]></evidence>
   Engineering writing is full of <, >, <=, >=, &, %, ^ and quotation marks.
   Inside CDATA you do NOT escape them and you MUST NOT escape them — copy
   them exactly as they appear. This is what keeps the output parseable.
3. NEVER put a verbatim quotation inside an XML attribute. Quotations always
   live in element text wrapped in CDATA. Attributes carry only short,
   controlled values (ids, section names, scores, priority labels).
4. Quote the SMALLEST span that proves your point — aim for under ~200
   characters per quote. Do not paste whole paragraphs or whole sections.
5. Keep the XML well-formed: open exactly one root element, close every tag,
   nest correctly, and write nothing outside the root element.
"""


# One fully worked criterion block. Shown to reviewers so the exact shape
# (reason -> evidence -> rubric level -> boundary test -> score -> confidence)
# and correct CDATA usage are unambiguous. It uses a fake criterion id and
# must never be copied into the actual answer.
REVIEWER_FORMAT_EXAMPLE = """
FORMAT EXAMPLE (illustration only — do NOT include this criterion in your
answer; use it purely to copy the structure and the CDATA style):

  <criterion id="example_criterion_ignore_me">
    <reasoning>The derivation in the results section is internally
    consistent and the reported error bounds follow from the stated model.
    One coefficient is quoted to more significant figures than the input
    data justify, but this does not change the conclusion.</reasoning>
    <evidence><![CDATA[Results: "the fitted gain k = 2.7431 gives R^2 > 0.99 for p < 0.01"]]></evidence>
    <rubric_level_matched>3</rubric_level_matched>
    <band_justification>Not a 4 because of the over-precise coefficient
    given the input resolution; not a 2 because there are no errors that
    threaten the validity of the result.</band_justification>
    <score>3</score>
    <confidence>High</confidence>
    <confidence_reason>The relevant equations and data are all present and
    legible, so little is left to interpretation.</confidence_reason>
  </criterion>
"""
