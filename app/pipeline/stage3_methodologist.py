"""
Stage 3: Methodologist Reviewer

Input:  llm (LLMService), sections (List[Dict])
Output: Dict with keys:
          reviewer_name (str)
          raw_xml       (str)
          scores        (Dict) — {criterion: {score, confidence, iqr, reasoning}}

Criteria:    methodology, critical_thinking, evidence_quality
Temperature: 0.3 (reviewer_temperature)
Self-consistency: Yes — 3 runs, median score, IQR-adjusted confidence
"""

import logging
import time
from typing import Any, Dict, List

from app.services.llm_service import LLMService
from app.config import get_settings
from app.prompts.stage3_methodologist_prompts import METHODOLOGIST_SYSTEM, METHODOLOGIST_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response, extract_scores_from_review
from app.pipeline import format_sections_for_prompt, compute_median_scores

logger = logging.getLogger(__name__)

METHODOLOGIST_CRITERIA = ["methodology", "critical_thinking", "evidence_quality"]
REVIEWER_NAME = "Methodologist"
XML_ROOT_TAG = "methodologist_review"


async def run(llm: LLMService, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run methodologist review with self-consistency sampling."""
    settings = get_settings()
    n_runs = settings.self_consistency_runs
    logger.info("Stage 3 (Methodologist) — starting %d self-consistency runs", n_runs)

    doc_sections_text = format_sections_for_prompt(sections)
    user_prompt = METHODOLOGIST_USER_TEMPLATE.format(document_sections=doc_sections_text)

    all_scores: List[Dict] = []
    last_raw_xml = ""

    for i in range(n_runs):
        t0 = time.perf_counter()
        logger.debug("Stage 3 — run %d/%d starting", i + 1, n_runs)
        try:
            raw = await llm.complete_with_retry(
                system_prompt=METHODOLOGIST_SYSTEM,
                user_prompt=user_prompt,
                temperature=settings.reviewer_temperature,
                max_tokens=4096,
            )
            parsed = parse_xml_response(raw, XML_ROOT_TAG)
            if parsed is not None:
                scores = extract_scores_from_review(parsed, METHODOLOGIST_CRITERIA)
                if scores:
                    all_scores.append(scores)
                    last_raw_xml = raw
                    logger.debug(
                        "Stage 3 — run %d/%d OK (%.2fs) — scores=%s",
                        i + 1, n_runs, time.perf_counter() - t0,
                        {k: v.get("score") for k, v in scores.items()},
                    )
                else:
                    logger.warning("Stage 3 — run %d/%d: XML parsed but no scores extracted", i + 1, n_runs)
            else:
                logger.warning("Stage 3 — run %d/%d: XML parse returned None", i + 1, n_runs)
        except Exception:
            logger.exception("Stage 3 — run %d/%d failed", i + 1, n_runs)

    if not all_scores:
        logger.error("Stage 3 — all %d self-consistency runs failed; using default scores", n_runs)
        return {
            "reviewer_name": REVIEWER_NAME,
            "raw_xml": "",
            "scores": {c: {"score": 2, "confidence": "low", "iqr": 0, "reasoning": ""} for c in METHODOLOGIST_CRITERIA},
        }

    median_scores = compute_median_scores(all_scores, METHODOLOGIST_CRITERIA)
    logger.info(
        "Stage 3 complete — %d/%d runs succeeded — median scores=%s",
        len(all_scores), n_runs,
        {k: v.get("score") for k, v in median_scores.items()},
    )
    return {
        "reviewer_name": REVIEWER_NAME,
        "raw_xml": last_raw_xml,
        "scores": median_scores,
    }
