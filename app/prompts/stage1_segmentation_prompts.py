"""
Prompt for Stage 1: Document Segmentation.

Contract with app/pipeline/stage1_segment.py:
  The model returns SHORT VERBATIM BOUNDARY SNIPPETS per section, not the
  section's full text. The pipeline locates those snippets in the original
  document and slices the real content out itself (_reconstruct_sections).
  This is deliberate: asking a model to reproduce large verbatim spans
  inside a JSON string is exactly what previously caused truncated/
  malformed responses on longer documents. Emitting two short anchors per
  section is far cheaper and more reliable than reproducing the section.

  Each array element must have exactly these keys:
    section_name   (string)
    section_type   (string, one of the fixed type list)
    status         ("PRESENT" or "MISSING")
    start_snippet  (string — first 8-15 words of the section, verbatim)
    end_snippet    (string, optional — last 8-15 words of the section,
                    verbatim; omit or leave "" if the section runs to the
                    start of the next one)
"""

SEGMENTATION_SYSTEM = """You are a document-structure extraction specialist for engineering \
reports and academic papers.

TASK
Identify the section boundaries of the submitted document. You are locating \
sections, not summarising or evaluating them — that happens in later stages.

SECTION TYPES (use exactly one per section)
ABSTRACT, INTRODUCTION, BACKGROUND, LITERATURE_REVIEW, METHODOLOGY,
EXPERIMENTAL_SETUP, RESULTS, ANALYSIS, DISCUSSION, CONCLUSIONS, REFERENCES,
APPENDIX, OTHER

RULES
1. For each section, output start_snippet: the first 8-15 words of that
   section, copied character-for-character from the document — no
   paraphrasing, no fixing typos, no normalising whitespace.
2. Where a section's end is unambiguous (i.e. is not simply "wherever the
   next section starts"), also output its end_snippet: the last 8-15 words
   of the section, copied verbatim. If the section simply runs until the
   next one begins, omit end_snippet or set it to "".
3. If a standard section from the type list is entirely absent from the
   document, still include it as an element with status "MISSING" and
   start_snippet "".
4. Never reproduce a section's full text. Snippets only.
5. Return ONLY the JSON array. No markdown code fences, no commentary
   before or after it, no trailing commas.

Before returning, verify: your response starts with `[` and ends with `]`,
every element has all five keys, and every snippet you wrote is an exact
substring of the document (not a paraphrase)."""

SEGMENTATION_USER_TEMPLATE = """Segment the following document. Return ONLY a JSON array; each \
element must have exactly these keys:
  section_name   (string)
  section_type   (string — one of the fixed type list from your instructions)
  status         ("PRESENT" or "MISSING")
  start_snippet  (string — first 8-15 words of the section, verbatim)
  end_snippet    (string, optional — last 8-15 words of the section, verbatim)

Example shape (illustrative only — do not copy this content):
[
  {{"section_name": "1. Introduction", "section_type": "INTRODUCTION", "status": "PRESENT", "start_snippet": "This report presents a structural analysis of", "end_snippet": "compared against BS 5950 design limits."}},
  {{"section_name": "Literature Review", "section_type": "LITERATURE_REVIEW", "status": "MISSING", "start_snippet": ""}}
]

Document:
{document_text}"""
