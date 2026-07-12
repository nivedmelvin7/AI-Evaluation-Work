"""
Stage 9: Feedback Synthesis

Input:  llm (LLMService),
        consensus_out  (Dict from stage 7),
        scoring_result (Dict from stage 8),
        sections       (List[Dict] from stage 1)
Output: Dict with keys:
          raw_xml              (str)
          overall_assessment   (str)
          strengths            (List[str])
          areas_for_improvement (List[Dict])
          recommended_actions  (str)
          closing              (str)

Temperature: 0.3
Self-consistency: No
"""

import json
import logging
import re
import time
from typing import Any, Dict, List

from app.services.llm_service import LLMService
from app.prompts.templates import FEEDBACK_SYSTEM, FEEDBACK_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response
from app.pipeline import format_sections_for_prompt

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_POINT_RE = re.compile(r"<point([^>]*)>(.*?)</point>", re.DOTALL)
_CITATION_LINE_RE = re.compile(
    r'<citation[^>]*section="([^"]*)"[^>]*quote="(.*)"\s*/?>'
)


def _strip_tags(text: str) -> str:
    return _TAG_RE.sub("", text).strip()


def _extract_block(raw: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
    return m.group(1) if m else ""


def _extract_point_text(point_body: str) -> str:
    m = re.search(r"<text>(.*?)</text>", point_body, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Backward-compat: no nested <text>; use the point body minus citations
    return _strip_tags(re.sub(r"<citation[^>]*/?>", "", point_body, flags=re.DOTALL))


def _extract_citations(point_body: str) -> List[Dict[str, Any]]:
    citations = []
    for line in point_body.split("\n"):
        m = _CITATION_LINE_RE.search(line)
        if m:
            citations.append({"section": m.group(1), "quote": m.group(2), "page": None})
    return citations


def _extract_points(raw: str, block_tag: str) -> List[Dict[str, Any]]:
    block = _extract_block(raw, block_tag)
    points = []
    for attrs, body in _POINT_RE.findall(block):
        text = _extract_point_text(body)
        if not text:
            continue
        entry = {"text": text, "citations": _extract_citations(body)}
        priority_m = re.search(r'priority="([^"]*)"', attrs)
        if priority_m:
            entry["priority"] = priority_m.group(1)
        points.append(entry)
    return points


def _regex_fallback_feedback(raw: str) -> Dict[str, Any]:
    """
    Best-effort recovery when the LLM's XML is too malformed to parse even
    after repair (e.g. a citation quote spanning multiple lines, or a
    response truncated mid-tag). Salvages whatever well-formed sections are
    still present instead of collapsing the entire feedback down to a raw,
    truncated text excerpt.
    """
    feedback: Dict[str, Any] = {}

    overall = _extract_block(raw, "overall_assessment")
    if overall:
        feedback["overall_assessment"] = _strip_tags(overall)

    strengths = [
        {"text": p["text"], "citations": p["citations"]}
        for p in _extract_points(raw, "strengths")
    ]
    if strengths:
        feedback["strengths"] = strengths

    improvements = [
        {"priority": p.get("priority", "medium"), "text": p["text"], "citations": p["citations"]}
        for p in _extract_points(raw, "areas_for_improvement")
    ]
    if improvements:
        feedback["areas_for_improvement"] = improvements

    recommended = _extract_block(raw, "recommended_actions")
    if recommended:
        feedback["recommended_actions"] = _strip_tags(recommended)

    closing = _extract_block(raw, "closing")
    if closing:
        feedback["closing"] = _strip_tags(closing)

    return feedback


async def run(
    llm: LLMService,
    consensus_out: Dict[str, Any],
    scoring_result: Dict[str, Any],
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Synthesise written feedback from consensus evaluation and scoring."""
    logger.info(
        "Stage 9 (feedback synthesis) — score=%.1f  grade=%s",
        scoring_result.get("final_score", 0),
        scoring_result.get("grade_band"),
    )

    doc_sections_text = format_sections_for_prompt(sections)

    consensus_text = consensus_out.get("raw_xml", "")
    if not consensus_text:
        consensus_text = json.dumps(consensus_out.get("scores", {}), indent=2)
        logger.debug("Stage 9 — no consensus XML; using JSON scores")

    scoring_text = json.dumps(
        {
            "final_score": scoring_result.get("final_score"),
            "grade_band": scoring_result.get("grade_band"),
            "penalised_score": scoring_result.get("penalised_score"),
            "confidence_interval": scoring_result.get("confidence_interval"),
            "gate_triggered": scoring_result.get("gate_triggered"),
            "deferred": scoring_result.get("deferred"),
            "criterion_breakdown": {
                k: {"score": v["level"], "confidence": v["confidence"]}
                for k, v in scoring_result.get("criterion_breakdown", {}).items()
            },
        },
        indent=2,
    )

    user_prompt = FEEDBACK_USER_TEMPLATE.format(
        consensus_output=consensus_text,
        scoring_output=scoring_text,
        document_sections=doc_sections_text,
    )

    t0 = time.perf_counter()
    try:
        raw = await llm.complete_with_retry(
            system_prompt=FEEDBACK_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception:
        logger.exception("Stage 9 — LLM call failed; returning empty feedback")
        return {
            "raw_xml": "",
            "overall_assessment": "Feedback generation failed.",
            "strengths": [],
            "areas_for_improvement": [],
            "recommended_actions": "",
            "closing": "",
        }

    logger.debug("Stage 9 — LLM response received (%.2fs, %d chars)", time.perf_counter() - t0, len(raw))

    parsed = parse_xml_response(raw, "feedback")
    feedback_dict: Dict[str, Any] = {"raw_xml": raw}

    if parsed is not None:
        overall_el = parsed.find("overall_assessment")
        if overall_el is not None and overall_el.text:
            feedback_dict["overall_assessment"] = overall_el.text.strip()

        strengths: List[Dict] = []
        for point_el in parsed.findall(".//strengths/point"):
            text_el = point_el.find("text")
            if text_el is not None and text_el.text:
                text = text_el.text.strip()
            else:
                # Backward-compat: old format had text directly in <point>
                text = (point_el.text or "").strip()
            citations = []
            for cit_el in point_el.findall("citation"):
                citations.append({
                    "section": cit_el.get("section", ""),
                    "quote": cit_el.get("quote", ""),
                    "page": None,
                })
            if text:
                strengths.append({"text": text, "citations": citations})
        feedback_dict["strengths"] = strengths

        improvements: List[Dict] = []
        for point_el in parsed.findall(".//areas_for_improvement/point"):
            text_el = point_el.find("text")
            if text_el is not None and text_el.text:
                text = text_el.text.strip()
            else:
                text = (point_el.text or "").strip()
            citations = []
            for cit_el in point_el.findall("citation"):
                citations.append({
                    "section": cit_el.get("section", ""),
                    "quote": cit_el.get("quote", ""),
                    "page": None,
                })
            if text:
                improvements.append({
                    "priority": point_el.get("priority", "medium"),
                    "text": text,
                    "citations": citations,
                })
        feedback_dict["areas_for_improvement"] = improvements

        rec_el = parsed.find("recommended_actions")
        if rec_el is not None and rec_el.text:
            feedback_dict["recommended_actions"] = rec_el.text.strip()

        closing_el = parsed.find("closing")
        if closing_el is not None and closing_el.text:
            feedback_dict["closing"] = closing_el.text.strip()

        logger.info(
            "Stage 9 complete — strengths=%d  improvements=%d",
            len(strengths),
            len(improvements),
        )
    else:
        logger.warning("Stage 9 — XML parse failed; attempting regex-based recovery")
        recovered = _regex_fallback_feedback(raw)
        if recovered.get("overall_assessment") or recovered.get("strengths") or recovered.get("areas_for_improvement"):
            feedback_dict["overall_assessment"] = recovered.get("overall_assessment", "")
            feedback_dict["strengths"] = recovered.get("strengths", [])
            feedback_dict["areas_for_improvement"] = recovered.get("areas_for_improvement", [])
            feedback_dict["recommended_actions"] = recovered.get("recommended_actions", "")
            feedback_dict["closing"] = recovered.get("closing", "")
            logger.info(
                "Stage 9 — regex recovery salvaged strengths=%d improvements=%d",
                len(feedback_dict["strengths"]), len(feedback_dict["areas_for_improvement"]),
            )
        else:
            logger.error("Stage 9 — regex recovery found nothing; returning raw text excerpt")
            feedback_dict["overall_assessment"] = raw[:500]
            feedback_dict["strengths"] = []
            feedback_dict["areas_for_improvement"] = []
            feedback_dict["recommended_actions"] = ""
            feedback_dict["closing"] = ""

    return feedback_dict
