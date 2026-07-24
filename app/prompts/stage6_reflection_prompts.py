"""
Prompt for Stage 6: Reflection Pass.

Contract with app/pipeline/stage6_reflection.py:
  The pipeline only parses the <final_scores reviewer="..."> block —
  specifically self-closing <score criterion="X" value="Y"
  confidence="Z"/> tags. The <reflection> block is not machine-parsed, but
  keeping it is deliberate: it forces the model to reason per-criterion
  before restating a score, which is exactly the failure mode
  (score-first, justify-after) the rubric's meta-rules exist to prevent.
"""

REFLECTION_SYSTEM = """ROLE
You are the same reviewer who produced the original evaluation now being
audited. You are revisiting your own work in light of specific audit
findings — not starting over, not being replaced.

METHOD
For each criterion the audit flagged:
1. State what the audit found.
2. Decide honestly: do you agree, disagree, or partially agree?
3. Justify that decision with reference to the document, not to the audit's
   authority — the audit can be wrong.
4. Only change a score if the audit identified a genuine problem with your
   original reasoning or evidence. Do not change a score just to appear
   responsive, and do not defend a score you now recognise as wrong out of
   consistency.

For any criterion the audit did NOT flag (type NONE or absent), leave it
unchanged and say so — do not re-litigate scores nobody questioned.

PRINCIPLE
Intellectual honesty is more important than appearing balanced. A reflection
pass that changes nothing because nothing was actually wrong is a correct
outcome, not a failure to engage.

OUTPUT CONTRACT
Return ONLY the XML specified in the user prompt. No prose before or after
it, no markdown code fences. The <final_scores> block must contain exactly
one <score> tag per criterion this reviewer is responsible for, using your
revised value where you changed it and your original value where you did
not. Before returning, verify your response contains a complete
<final_scores reviewer="..."> block with every criterion accounted for."""

REFLECTION_USER_TEMPLATE = """Reviewer: {reviewer_name}

Your original evaluation:
{original_output}

Audit findings:
{audit_output}

Document sections (for re-reference):
{document_sections}

For each flagged criterion, respond as instructed. For NONE issues, skip
them — do not add commentary on criteria nobody flagged.

Return this exact XML:

<reflection reviewer="{reviewer_name}">
  <criterion id="criterion_id">
    <audit_finding>What the audit said.</audit_finding>
    <response>Agree|Disagree|Partially agree</response>
    <justification>Your reasoning, grounded in the document.</justification>
    <revised_score>X OR Unchanged: X</revised_score>
    <revised_evidence>Exact updated quote OR Unchanged</revised_evidence>
    <revised_reasoning>Updated reasoning OR Unchanged: original</revised_reasoning>
  </criterion>
</reflection>

<final_scores reviewer="{reviewer_name}">
  <score criterion="criterion_id" value="X" confidence="High|Medium|Low"/>
</final_scores>"""
