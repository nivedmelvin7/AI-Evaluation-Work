"""
Stage 10: Verification Guard

Input:  llm (LLMService),
        feedback_out       (Dict from stage 9),
        full_document_text (str — original document)
Output: Dict with keys:
          raw_xml              (str)
          overall_integrity    (str) — PASS | FLAG | FAIL
          final_recommendation (str) — RELEASE | HOLD | REJECT
          injection_found      (bool)
          detected_patterns    (List[Dict])
          factual_summary      (str)
          release_note         (str)

Temperature: 0.0 (deterministic)
Self-consistency: No
"""

import logging
import time
from typing import Any, Dict

from app.services.llm_service import LLMService
from app.prompts.templates import VERIFICATION_SYSTEM, VERIFICATION_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response

logger = logging.getLogger(__name__)

# Cap document text sent to verifier to avoid token limits
_VERIFICATION_DOC_CHAR_LIMIT = 20000


async def run(
    llm: LLMService,
    feedback_out: Dict[str, Any],
    full_document_text: str,
) -> Dict[str, Any]:
    """Run factual verification and injection detection on the feedback."""
    logger.info("Stage 10 (verification) — checking feedback integrity")

    feedback_xml = feedback_out.get("raw_xml", "")
    if not feedback_xml:
        feedback_xml = feedback_out.get("overall_assessment", str(feedback_out))
        logger.debug("Stage 10 — no feedback XML; using overall_assessment text")

    doc_excerpt = full_document_text[:_VERIFICATION_DOC_CHAR_LIMIT]
    if len(full_document_text) > _VERIFICATION_DOC_CHAR_LIMIT:
        logger.debug(
            "Stage 10 — document truncated from %d to %d chars for verifier",
            len(full_document_text),
            _VERIFICATION_DOC_CHAR_LIMIT,
        )

    user_prompt = VERIFICATION_USER_TEMPLATE.format(
        feedback_output=feedback_xml,
        full_document_text=doc_excerpt,
    )

    t0 = time.perf_counter()
    try:
        raw = await llm.complete_with_retry(
            system_prompt=VERIFICATION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception:
        logger.exception("Stage 10 — LLM call failed; defaulting to PASS/RELEASE")
        return _default_verification()

    logger.debug("Stage 10 — LLM response received (%.2fs, %d chars)", time.perf_counter() - t0, len(raw))

    parsed = parse_xml_response(raw, "verification")

    result: Dict[str, Any] = {
        "raw_xml": raw,
        "overall_integrity": "PASS",
        "final_recommendation": "RELEASE",
        "injection_found": False,
        "detected_patterns": [],
        "factual_summary": "",
        "release_note": "",
    }

    if parsed is None:
        logger.warning("Stage 10 — XML parse failed; defaulting to PASS/RELEASE")
        return result

    integrity_el = parsed.find("overall_integrity")
    if integrity_el is not None and integrity_el.text:
        result["overall_integrity"] = integrity_el.text.strip()

    rec_el = parsed.find("final_recommendation")
    if rec_el is not None and rec_el.text:
        result["final_recommendation"] = rec_el.text.strip()

    injection_el = parsed.find(".//injection_found")
    if injection_el is not None and injection_el.text:
        result["injection_found"] = injection_el.text.strip().lower() == "yes"

    release_note_el = parsed.find("release_note")
    if release_note_el is not None and release_note_el.text:
        result["release_note"] = release_note_el.text.strip()

    factual_summary_el = parsed.find(".//factual_summary")
    if factual_summary_el is not None and factual_summary_el.text:
        result["factual_summary"] = factual_summary_el.text.strip()

    patterns = []
    for pattern_el in parsed.findall(".//pattern"):
        type_el = pattern_el.find("type")
        location_el = pattern_el.find("location")
        content_el = pattern_el.find("content")
        intent_el = pattern_el.find("intent")
        patterns.append({
            "type": type_el.text.strip() if type_el is not None and type_el.text else "",
            "location": location_el.text.strip() if location_el is not None and location_el.text else "",
            "content": content_el.text.strip() if content_el is not None and content_el.text else "",
            "intent": intent_el.text.strip() if intent_el is not None and intent_el.text else "",
        })
    result["detected_patterns"] = patterns

    logger.info(
        "Stage 10 complete — integrity=%s  recommendation=%s  injection=%s  patterns=%d",
        result["overall_integrity"],
        result["final_recommendation"],
        result["injection_found"],
        len(patterns),
    )

    if result["injection_found"]:
        logger.warning(
            "Stage 10 — PROMPT INJECTION DETECTED — %d pattern(s): %s",
            len(patterns),
            [p.get("type") for p in patterns],
        )

    if result["final_recommendation"] == "REJECT":
        logger.error(
            "Stage 10 — REJECT recommendation — evaluation should not be released without review"
        )
        result["rejection_warning"] = (
            "Verification stage flagged this evaluation for rejection. "
            "Results are included but should not be released without manual review."
        )

    return result


def _default_verification() -> Dict[str, Any]:
    return {
        "raw_xml": "",
        "overall_integrity": "PASS",
        "final_recommendation": "RELEASE",
        "injection_found": False,
        "detected_patterns": [],
        "factual_summary": "Verification skipped due to LLM error.",
        "release_note": "Verification could not be completed.",
    }
