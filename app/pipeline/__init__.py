"""
Shared pipeline utilities: section formatting and self-consistency scoring.
"""

from typing import Dict, Any, List
from app.config import get_settings


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


def compute_median_scores(
    all_scores: List[Dict[str, Dict[str, Any]]],
    criteria: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Given N runs of reviewer scores, return the median score per criterion
    with IQR-adjusted confidence.
    """
    median_scores: Dict[str, Dict[str, Any]] = {}

    for criterion in criteria:
        values = [
            s[criterion]["score"]
            for s in all_scores
            if criterion in s
        ]
        confs = [
            s[criterion]["confidence"]
            for s in all_scores
            if criterion in s
        ]
        reasonings = [
            s[criterion].get("reasoning", "")
            for s in all_scores
            if criterion in s
        ]

        if not values:
            median_scores[criterion] = {
                "score": 2,
                "confidence": "low",
                "iqr": 0,
                "reasoning": "",
            }
            continue

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        median = sorted_vals[n // 2]
        iqr = sorted_vals[-1] - sorted_vals[0]

        base_conf = confs[n // 2] if confs else "medium"
        if iqr >= 2:
            conf = "low"
        elif iqr == 1:
            conf = "medium" if base_conf == "high" else base_conf
        else:
            conf = base_conf

        median_scores[criterion] = {
            "score": median,
            "confidence": conf,
            "iqr": iqr,
            "reasoning": reasonings[n // 2] if reasonings else "",
        }

    return median_scores
