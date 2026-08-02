"""
Shared pipeline utilities: section formatting and self-consistency scoring.
"""

from typing import Dict, Any, List
from app.config import get_settings
from app.models.assessment import CONFIDENCE_RANK


def format_sections_for_prompt(sections: List[Dict[str, Any]]) -> str:
    """Format parsed sections into a prompt-ready string, truncating to MAX_SECTION_CHARS."""
    settings = get_settings()
    max_chars = settings.max_section_chars
    parts = []
    for s in sections:
        if s.get("status") == "MISSING":
            continue
        content = s.get("content", "")
        if len(content) > max_chars:
            content = content[:max_chars] + "\n[... section truncated ...]"
        parts.append(
            f"=== {s['section_name']} ({s['section_type']}) ===\n{content}"
        )
    return "\n\n".join(parts)


def sections_as_document_text(sections: List[Dict[str, Any]]) -> str:
    """Return all parsed submission text for evidence verification.

    Unlike prompt formatting this does not truncate content: a quote is valid
    only when it really appears in the submitted document/parsed sections.
    """
    return "\n\n".join(
        str(section.get("content", ""))
        for section in sections
        if section.get("status") != "MISSING"
    )


def compute_median_scores(
    all_scores: List[Dict[str, Dict[str, Any]]],
    criteria: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Given complete valid reviewer runs, return an aligned structured median.

    The representative assessment is one real run whose score equals the
    median. It is selected by highest valid confidence and then earliest run,
    so reasoning and evidence can never be borrowed from another response.
    """
    median_scores: Dict[str, Dict[str, Any]] = {}

    for criterion in criteria:
        assessments = [s[criterion] for s in all_scores if criterion in s]
        if len(assessments) != len(all_scores):
            # A partial reviewer run is not a valid source for a median.
            continue

        sorted_vals = sorted(assessment["score"] for assessment in assessments)
        n = len(sorted_vals)
        median = sorted_vals[n // 2]
        score_range = sorted_vals[-1] - sorted_vals[0]
        candidates = [assessment for assessment in assessments if assessment["score"] == median]
        representative = min(
            candidates,
            key=lambda assessment: (
                -CONFIDENCE_RANK[assessment["confidence"]],
                assessment.get("source_run", 0),
            ),
        )
        median_assessment = dict(representative)
        base_conf = median_assessment["confidence"]
        if score_range >= 2:
            conf = "low"
        elif score_range == 1:
            conf = "medium" if base_conf == "high" else base_conf
        else:
            conf = base_conf
        median_assessment["confidence"] = conf
        median_assessment["score_range"] = score_range
        median_assessment["runs_succeeded"] = len(all_scores)
        median_scores[criterion] = median_assessment

    return median_scores
