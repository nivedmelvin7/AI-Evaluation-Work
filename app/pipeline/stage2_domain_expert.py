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

import sys
from typing import List, Dict, Any

from app.services.llm_service import LLMService
from app.config import get_settings
from app.prompts.templates import DOMAIN_EXPERT_SYSTEM, DOMAIN_EXPERT_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response, extract_scores_from_review
from app.pipeline import format_sections_for_prompt, compute_median_scores

DOMAIN_CRITERIA = ["technical_accuracy", "methodology", "evidence_quality"]
REVIEWER_NAME = "Domain Expert"
XML_ROOT_TAG = "domain_expert_review"


async def run(llm: LLMService, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run domain expert review with self-consistency sampling."""
    settings = get_settings()
    doc_sections_text = format_sections_for_prompt(sections)
    user_prompt = DOMAIN_EXPERT_USER_TEMPLATE.format(document_sections=doc_sections_text)

    all_scores: List[Dict] = []
    last_raw_xml = ""

    for i in range(settings.self_consistency_runs):
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
        except Exception as e:
            print(f"[Stage 2] Run {i + 1} failed: {e}", file=sys.stderr)

    if not all_scores:
        print(f"[Stage 2] All self-consistency runs failed — using defaults.", file=sys.stderr)
        return {
            "reviewer_name": REVIEWER_NAME,
            "raw_xml": "",
            "scores": {c: {"score": 2, "confidence": "low", "iqr": 0, "reasoning": ""} for c in DOMAIN_CRITERIA},
        }

    median_scores = compute_median_scores(all_scores, DOMAIN_CRITERIA)

    return {
        "reviewer_name": REVIEWER_NAME,
        "raw_xml": last_raw_xml,
        "scores": median_scores,
    }
