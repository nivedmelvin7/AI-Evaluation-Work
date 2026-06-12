from lxml import etree
from typing import Optional, Dict, Any
import re


def parse_xml_response(raw: str, root_tag: str) -> Optional[etree._Element]:
    """
    Extract and parse XML from a raw LLM response.
    Returns the root element or None on failure.
    """
    raw = re.sub(r"```xml\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()

    start = raw.find(f"<{root_tag}")
    end = raw.rfind(f"</{root_tag}>")
    if start == -1 or end == -1:
        return None
    xml_str = raw[start: end + len(f"</{root_tag}>")]

    try:
        return etree.fromstring(xml_str.encode("utf-8"))
    except etree.XMLSyntaxError:
        # Attempt light repair: escape unescaped ampersands
        xml_str = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&amp;", xml_str)
        try:
            return etree.fromstring(xml_str.encode("utf-8"))
        except Exception:
            return None


def extract_scores_from_review(
    xml_root: etree._Element,
    criteria: list[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Extract score and confidence for each criterion from a reviewer XML element.
    Returns {criterion_id: {"score": int, "confidence": str, "reasoning": str}}
    """
    scores = {}
    for criterion_id in criteria:
        el = xml_root.find(f".//criterion[@id='{criterion_id}']")
        if el is None:
            continue
        score_el = el.find("score")
        confidence_el = el.find("confidence")
        reasoning_el = el.find("reasoning")
        revised_score_el = el.find("revised_score")

        # Use revised score if present (from reflection stage)
        score_text = (
            revised_score_el.text if revised_score_el is not None
            else score_el.text if score_el is not None
            else None
        )
        if score_text:
            score_text = score_text.strip()
            # Handle "Unchanged: 3" format from reflection
            if score_text.lower().startswith("unchanged"):
                match = re.search(r"\d", score_text)
                score_val = int(match.group()) if match else 2
            else:
                try:
                    score_val = int(score_text)
                except ValueError:
                    score_val = 2
        else:
            score_val = 2

        scores[criterion_id] = {
            "score": max(0, min(4, score_val)),
            "confidence": confidence_el.text.strip().lower()
            if confidence_el is not None else "medium",
            "reasoning": reasoning_el.text.strip()
            if reasoning_el is not None else "",
        }
    return scores
