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

Two independent checks feed the verdict:
  1. Factual verification — an LLM call (see app/prompts/stage10_verification_prompts.py)
     that checks the feedback's claims against the actual document.
  2. Prompt-injection scanning — a deterministic, non-LLM scan of the raw
     document (app/security/prompt_injection_scanner.py), run separately by
     the orchestrator and passed in here.

They are combined in code (_combine), not by asking the LLM to reason about
both — the scan result is not something an LLM verdict should be able to
override, since the whole point of a deterministic scanner is that it can't
be talked out of a finding the way a model sharing a context window with
the attack could be.

Temperature: 0.0 (deterministic)
Self-consistency: No
"""

import logging
import time
from typing import Any, Dict, Optional

from app.services.llm_service import LLMService
from app.prompts.stage10_verification_prompts import VERIFICATION_SYSTEM, VERIFICATION_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response
from app.security.prompt_injection_scanner import ScanResult, RiskLevel

logger = logging.getLogger(__name__)

# Cap document text sent to the factual verifier to avoid token limits. The
# security scanner, in contrast, runs over the complete, untruncated
# document — it's cheap and there's no reason to give an attacker a "hide
# past the truncation point" strategy against it.
_VERIFICATION_DOC_CHAR_LIMIT = 20000

_INTEGRITY_RANK = {"PASS": 0, "FLAG": 1, "FAIL": 2}
_RANK_TO_INTEGRITY = {0: "PASS", 1: "FLAG", 2: "FAIL"}
_RANK_TO_RECOMMENDATION = {0: "RELEASE", 1: "HOLD", 2: "REJECT"}
_SCAN_RANK = {RiskLevel.NONE: 0, RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}


async def run(
    llm: LLMService,
    feedback_out: Dict[str, Any],
    full_document_text: str,
    injection_scan: ScanResult,
) -> Dict[str, Any]:
    """Run factual verification and combine it with the security scan."""
    logger.info("Stage 10 (verification) — checking feedback integrity")

    feedback_xml = feedback_out.get("raw_xml", "")
    if not feedback_xml:
        feedback_xml = feedback_out.get("overall_assessment", str(feedback_out))
        logger.debug("Stage 10 — no feedback XML; using overall_assessment text")

    doc_excerpt = full_document_text[:_VERIFICATION_DOC_CHAR_LIMIT]
    if len(full_document_text) > _VERIFICATION_DOC_CHAR_LIMIT:
        logger.debug(
            "Stage 10 — document truncated from %d to %d chars for factual verifier",
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
        logger.exception("Stage 10 — factual-verification LLM call failed")
        return _combine(
            raw_xml="",
            factual_integrity="FLAG",
            factual_summary="Factual verification could not be completed due to an LLM error.",
            llm_release_note=None,
            injection_scan=injection_scan,
        )

    logger.debug("Stage 10 — LLM response received (%.2fs, %d chars)", time.perf_counter() - t0, len(raw))

    parsed = parse_xml_response(raw, "verification")
    if parsed is None:
        logger.warning("Stage 10 — factual-verification XML parse failed")
        return _combine(
            raw_xml=raw,
            factual_integrity="FLAG",
            factual_summary="Factual verification response could not be parsed.",
            llm_release_note=None,
            injection_scan=injection_scan,
        )

    factual_integrity = "FLAG"
    integrity_el = parsed.find("factual_integrity")
    if integrity_el is not None and integrity_el.text and integrity_el.text.strip().upper() in _INTEGRITY_RANK:
        factual_integrity = integrity_el.text.strip().upper()

    factual_summary = ""
    summary_el = parsed.find(".//factual_summary")
    if summary_el is not None and summary_el.text:
        factual_summary = summary_el.text.strip()

    llm_release_note = None
    release_note_el = parsed.find("release_note")
    if release_note_el is not None and release_note_el.text:
        llm_release_note = release_note_el.text.strip()

    return _combine(
        raw_xml=raw,
        factual_integrity=factual_integrity,
        factual_summary=factual_summary,
        llm_release_note=llm_release_note,
        injection_scan=injection_scan,
    )


def _combine(
    raw_xml: str,
    factual_integrity: str,
    factual_summary: str,
    llm_release_note: Optional[str],
    injection_scan: ScanResult,
) -> Dict[str, Any]:
    """Deterministically merge the factual verdict with the security scan.
    Whichever side is worse wins — a clean factual check does not soften a
    high-risk scan finding, and a high-risk scan finding does not get
    argued down by a clean factual check."""
    factual_rank = _INTEGRITY_RANK.get(factual_integrity, 1)
    scan_rank = _SCAN_RANK[injection_scan.risk_level]
    combined_rank = max(factual_rank, scan_rank)

    overall_integrity = _RANK_TO_INTEGRITY[combined_rank]
    final_recommendation = _RANK_TO_RECOMMENDATION[combined_rank]

    if scan_rank >= factual_rank and scan_rank > 0:
        n = len(injection_scan.detected_patterns)
        release_note = (
            f"Automated document scan found {n} suspicious pattern(s) "
            f"(risk: {injection_scan.risk_level.value}) — {final_recommendation.lower()} recommended."
        )
    else:
        release_note = llm_release_note or "Factual verification completed."

    result: Dict[str, Any] = {
        "raw_xml": raw_xml,
        "overall_integrity": overall_integrity,
        "final_recommendation": final_recommendation,
        "injection_found": injection_scan.injection_found,
        "detected_patterns": [p.to_dict() for p in injection_scan.detected_patterns],
        "factual_summary": factual_summary,
        "release_note": release_note,
    }

    logger.info(
        "Stage 10 complete — factual=%s  scan=%s  combined=%s/%s  patterns=%d",
        factual_integrity,
        injection_scan.risk_level.value,
        overall_integrity,
        final_recommendation,
        len(injection_scan.detected_patterns),
    )

    if injection_scan.injection_found:
        logger.warning(
            "Stage 10 — SECURITY SCAN FLAGGED %d pattern(s): %s",
            len(injection_scan.detected_patterns),
            [p.type for p in injection_scan.detected_patterns],
        )

    if final_recommendation == "REJECT":
        logger.error("Stage 10 — REJECT recommendation — evaluation should not be released without review")
        result["rejection_warning"] = (
            "Verification stage flagged this evaluation for rejection. "
            "Results are included but should not be released without manual review."
        )

    return result
