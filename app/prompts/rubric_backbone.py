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
RULE 1: Every judgement MUST cite a specific quoted passage from
        the document. Format: [Section: "exact quoted text"]
RULE 2: Do NOT reward length for its own sake.
RULE 3: Do NOT penalise non-native English fluency if technical
        content is sound.
RULE 4: Do NOT be influenced by confident tone when content is wrong.
RULE 5: Reason fully before assigning any score. Never score first.
RULE 6: Express confidence in every score: High, Medium, or Low.
"""
