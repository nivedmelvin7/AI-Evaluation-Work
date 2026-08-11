from lxml import etree
from typing import Optional, Dict, Any, Iterable, List, Tuple
import re

from app.models.assessment import validate_complete_assessments
from app.rubric import ALL_CRITERIA

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


def _text(element: Optional[etree._Element]) -> str:
    return "".join(element.itertext()).strip() if element is not None else ""


def _strict_integer(value: str) -> Any:
    """Keep invalid XML values invalid; never coerce them into a rubric level."""
    value = value.strip()
    if not re.fullmatch(r"[0-4]", value):
        return value
    return int(value)


def parse_review_assessments(
    xml_root: etree._Element,
    criteria: Iterable[str],
    document_text: str,
    source_reviewer: str,
    source_run: int,
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """Parse a complete reviewer response while preserving usable evidence.

    Structural issues (missing criteria, invalid levels, empty reasoning, and
    broken boundary justification) remain errors.  A quotation that cannot be
    matched exactly after PDF extraction is retained as an explicit warning on
    the assessment; it reduces confidence later instead of erasing a genuine
    content judgement.
    """
    expected = tuple(criteria)
    payloads: List[Dict[str, Any]] = []
    errors: List[str] = []
    seen: set[str] = set()
    for criterion_el in xml_root.findall(".//criterion"):
        criterion_id = criterion_el.get("id", "").strip()
        if criterion_id in seen:
            errors.append(f"duplicate criterion: {criterion_id or 'missing id'}")
            continue
        seen.add(criterion_id)
        if criterion_id not in expected:
            errors.append(f"unexpected criterion: {criterion_id or 'missing id'}")
            continue

        score_text = _text(criterion_el.find("score"))
        rubric_level_text = _text(criterion_el.find("rubric_level_matched"))
        if not rubric_level_text:
            errors.append(f"{criterion_id}: missing rubric_level_matched")
        elif rubric_level_text != score_text:
            errors.append(f"{criterion_id}: rubric_level_matched must equal score")
        payloads.append({
            "criterion_id": criterion_id,
            "score": _strict_integer(score_text) if score_text else None,
            "confidence": _text(criterion_el.find("confidence")),
            "reasoning": _text(criterion_el.find("reasoning")),
            "evidence": _text(criterion_el.find("evidence")),
            "band_justification": _text(criterion_el.find("band_justification")),
            "confidence_reason": _text(criterion_el.find("confidence_reason")),
            "source_reviewer": source_reviewer,
            "source_run": source_run,
        })
    scores, validation_errors = validate_complete_assessments(
        payloads,
        expected,
        document_text,
        allow_unverified_evidence=True,
    )
    return scores, errors + validation_errors


def extract_scores_from_review(
    xml_root: etree._Element,
    criteria: list[str],
    document_text: str = "",
    source_reviewer: str = "Unknown reviewer",
    source_run: int = 1,
) -> Dict[str, Dict[str, Any]]:
    """Compatibility wrapper returning only a complete, valid assessment map.

    Code that needs diagnostics must use :func:`parse_review_assessments`.
    An incomplete or malformed response returns an empty map instead of a
    plausible-looking score map.
    """
    scores, errors = parse_review_assessments(
        xml_root, criteria, document_text, source_reviewer, source_run
    )
    return {} if errors else scores
