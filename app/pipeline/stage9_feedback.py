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
import sys
from typing import Dict, Any, List

from app.services.llm_service import LLMService
from app.prompts.templates import FEEDBACK_SYSTEM, FEEDBACK_USER_TEMPLATE
from app.utils.xml_parser import parse_xml_response
from app.pipeline import format_sections_for_prompt


async def run(
    llm: LLMService,
    consensus_out: Dict[str, Any],
    scoring_result: Dict[str, Any],
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Synthesise written feedback from consensus evaluation and scoring."""
    doc_sections_text = format_sections_for_prompt(sections)

    consensus_text = consensus_out.get("raw_xml", "")
    if not consensus_text:
        consensus_text = json.dumps(consensus_out.get("scores", {}), indent=2)

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

    try:
        raw = await llm.complete_with_retry(
            system_prompt=FEEDBACK_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        print(f"[Stage 9] LLM call failed: {e}", file=sys.stderr)
        return {"raw_xml": "", "overall_assessment": "Feedback generation failed.", "strengths": [], "areas_for_improvement": [], "recommended_actions": "", "closing": ""}

    parsed = parse_xml_response(raw, "feedback")

    feedback_dict: Dict[str, Any] = {"raw_xml": raw}

    if parsed is not None:
        overall_el = parsed.find("overall_assessment")
        if overall_el is not None and overall_el.text:
            feedback_dict["overall_assessment"] = overall_el.text.strip()

        strengths: List[str] = []
        for point_el in parsed.findall(".//strengths/point"):
            if point_el.text:
                strengths.append(point_el.text.strip())
        feedback_dict["strengths"] = strengths

        improvements: List[Dict[str, str]] = []
        for point_el in parsed.findall(".//areas_for_improvement/point"):
            improvements.append({
                "priority": point_el.get("priority", "medium"),
                "text": point_el.text.strip() if point_el.text else "",
            })
        feedback_dict["areas_for_improvement"] = improvements

        rec_el = parsed.find("recommended_actions")
        if rec_el is not None and rec_el.text:
            feedback_dict["recommended_actions"] = rec_el.text.strip()

        closing_el = parsed.find("closing")
        if closing_el is not None and closing_el.text:
            feedback_dict["closing"] = closing_el.text.strip()
    else:
        print("[Stage 9] XML parse failed — returning raw text.", file=sys.stderr)
        feedback_dict["overall_assessment"] = raw[:500]

    return feedback_dict
