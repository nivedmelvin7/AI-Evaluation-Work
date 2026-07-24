from lxml import etree
from typing import Optional, Dict, Any
import re

_ATTR_START_RE = re.compile(r'\w+="')


def _escape_attr_value(value: str) -> str:
    # `&` is handled separately (see _fix_ampersands) so entities that are
    # already well-formed (e.g. "&amp;") aren't double-escaped here.
    return value.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _repair_attribute_values(xml_str: str) -> str:
    """
    LLM output frequently embeds verbatim document text inside attribute
    values (e.g. a citation's quote="..."). That text often contains
    characters like <, >, or " (e.g. "p < 0.05", a quoted term) which break
    attribute parsing if left as-is. Re-escape attribute values, scanning
    line by line, bounding each value between its own opening `attr="` and
    the next attribute's start (or end of line) so a fix for one attribute
    can't swallow neighboring ones on the same line.
    """
    def fix_line(line: str) -> str:
        starts = list(_ATTR_START_RE.finditer(line))
        if not starts:
            return line
        pieces = []
        cursor = 0
        for i, m in enumerate(starts):
            value_start = m.end()
            window_end = starts[i + 1].start() if i + 1 < len(starts) else len(line)
            window = line[value_start:window_end]
            last_quote = window.rfind('"')
            if last_quote == -1:
                continue
            pieces.append(line[cursor:value_start])
            pieces.append(_escape_attr_value(window[:last_quote]))
            pieces.append('"')
            cursor = value_start + last_quote + 1
        pieces.append(line[cursor:])
        return "".join(pieces)
    return "\n".join(fix_line(line) for line in xml_str.split("\n"))


def _fix_ampersands(xml_str: str) -> str:
    return re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&amp;", xml_str)


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
        pass

    # Repair 1: re-escape attribute values (the usual break — verbatim
    # quotes copied from the source document containing <, >, or ").
    repaired = _repair_attribute_values(xml_str)
    try:
        return etree.fromstring(repaired.encode("utf-8"))
    except etree.XMLSyntaxError:
        pass

    # Repair 2: escape stray ampersands anywhere else in the document
    repaired = _fix_ampersands(repaired)
    try:
        return etree.fromstring(repaired.encode("utf-8"))
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
