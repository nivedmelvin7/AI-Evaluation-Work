"""
Stage 2: Domain Expert Reviewer

Input:  llm (LLMService), sections (List[Dict])
Output: Dict with keys:
          reviewer_name (str)
          raw_xml       (str) — representative XML from median run
          scores        (Dict) — {criterion: {score, confidence, iqr, reasoning}}

Criteria:    technical_accuracy, methodology, evidence_quality
Temperature: 0.3 (reviewer_temperature)
Self-consistency: Yes — 3 runs, median score, IQR-adjusted confidence
"""

import logging
import time
from typing import Any, Dict, List

from app.services.llm_service import LLMService
from app.config import get_settings
from app.prompts.templates import DOMAIN_EXPERT_SYSTEM, DOMAIN_EXPERT_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response, extract_scores_from_review
from app.pipeline import format_sections_for_prompt, compute_median_scores

logger = logging.getLogger(__name__)

DOMAIN_CRITERIA = ["technical_accuracy", "methodology", "evidence_quality"]
REVIEWER_NAME = "Domain Expert"
XML_ROOT_TAG = "domain_expert_review"


async def run(llm: LLMService, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run domain expert review with self-consistency sampling."""
    settings = get_settings()
    n_runs = settings.self_consistency_runs
    logger.info("Stage 2 (Domain Expert) — starting %d self-consistency runs", n_runs)

    doc_sections_text = format_sections_for_prompt(sections)
    user_prompt = DOMAIN_EXPERT_USER_TEMPLATE.format(document_sections=doc_sections_text)

    all_scores: List[Dict] = []
    last_raw_xml = ""

    for i in range(n_runs):
        t0 = time.perf_counter()
        logger.debug("Stage 2 — run %d/%d starting", i + 1, n_runs)
        try:
            raw = await llm.complete_with_retry(
                system_prompt=DOMAIN_EXPERT_SYSTEM,
                user_prompt=user_prompt,
                temperature=settings.reviewer_temperature,
                max_tokens=4096,
            )
            parsed = parse_xml_response(raw, XML_ROOT_TAG)
            if parsed is not None:
                scores = extract_scores_from_review(parsed, DOMAIN_CRITERIA)
                if scores:
                    all_scores.append(scores)
                    last_raw_xml = raw
                    logger.debug(
                        "Stage 2 — run %d/%d OK (%.2fs) — scores=%s",
                        i + 1, n_runs, time.perf_counter() - t0,
                        {k: v.get("score") for k, v in scores.items()},
                    )
                else:
                    logger.warning("Stage 2 — run %d/%d: XML parsed but no scores extracted", i + 1, n_runs)
            else:
                logger.warning("Stage 2 — run %d/%d: XML parse returned None", i + 1, n_runs)
        except Exception:
            logger.exception("Stage 2 — run %d/%d failed", i + 1, n_runs)

    if not all_scores:
        logger.error("Stage 2 — all %d self-consistency runs failed; using default scores", n_runs)
        return {
            "reviewer_name": REVIEWER_NAME,
            "raw_xml": "",
            "scores": {c: {"score": 2, "confidence": "low", "iqr": 0, "reasoning": ""} for c in DOMAIN_CRITERIA},
        }

    median_scores = compute_median_scores(all_scores, DOMAIN_CRITERIA)
    logger.info(
        "Stage 2 complete — %d/%d runs succeeded — median scores=%s",
        len(all_scores), n_runs,
        {k: v.get("score") for k, v in median_scores.items()},
    )
    return {
        "reviewer_name": REVIEWER_NAME,
        "raw_xml": last_raw_xml,
        "scores": median_scores,
    }
