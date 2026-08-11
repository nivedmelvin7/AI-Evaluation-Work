"""
Pipeline orchestrator. Runs all 10 stages in sequence.
"""

import logging
import time
import uuid

from app.services.llm_service import LLMService
from app.services.document_service import DocumentService
from app.services import session_service
from app.db.session import AsyncSessionLocal
from app.pipeline import (
    stage1_segment,
    stage2_domain_expert,
    stage3_methodologist,
    stage4_communication,
    stage5_self_critique,
    stage6_reflection,
    stage7_consensus,
    stage8_scoring,
    stage9_feedback,
    stage10_verification,
)
from app.models.response_models import EvaluationResult
from app.security.prompt_injection_scanner import scan_document

logger = logging.getLogger(__name__)


def _elapsed(t0: float) -> str:
    return f"{time.perf_counter() - t0:.2f}s"


class PipelineOrchestrator:

    def __init__(self):
        self.llm = LLMService()
        self.doc_service = DocumentService()

    async def run(
        self,
        version_id: uuid.UUID,
        document_text: str,
        pages: list = None,
        *,
        mark_failed: bool = True,
    ) -> EvaluationResult:
        job_id = str(version_id)
        pipeline_start = time.perf_counter()
        logger.info(
            "[%s] Pipeline started — document length=%d chars",
            job_id,
            len(document_text),
        )

        async with AsyncSessionLocal() as db:
            await session_service.update_version(
                db, version_id, status="running", stage="segmentation", progress=5
            )

            try:
                # ----------------------------------------------------------------
                # Security scan (deterministic, no LLM call) — runs before any
                # stage sees the document. Its verdict is threaded through to
                # Stage 10, where it is combined with factual verification.
                # ----------------------------------------------------------------
                injection_scan = scan_document(document_text)
                if injection_scan.injection_found:
                    logger.warning(
                        "[%s] Security scan — risk=%s recommendation=%s patterns=%s",
                        job_id,
                        injection_scan.risk_level.value,
                        injection_scan.recommendation,
                        [p.type for p in injection_scan.detected_patterns],
                    )

                # ----------------------------------------------------------------
                # Stage 1: Segmentation
                # ----------------------------------------------------------------
                t = time.perf_counter()
                logger.info("[%s] Stage 1 (segmentation) — starting", job_id)
                sections = await stage1_segment.run(self.llm, document_text)
                logger.info(
                    "[%s] Stage 1 complete — %d sections found (%s)",
                    job_id,
                    len(sections),
                    _elapsed(t),
                )
                for i, s in enumerate(sections):
                    logger.debug(
                        "[%s]   section[%d] name=%r  type=%s  words=%d  status=%s",
                        job_id,
                        i,
                        s.get("section_name"),
                        s.get("section_type"),
                        s.get("word_count", 0),
                        s.get("status"),
                    )
                await session_service.update_version(db, version_id, stage="reviewing", progress=15)

                # ----------------------------------------------------------------
                # Stages 2+3+4: Sequential reviewer pass
                # ----------------------------------------------------------------
                t = time.perf_counter()
                logger.info("[%s] Stages 2-4 (sequential reviewer pass) — starting", job_id)
                de_out = await stage2_domain_expert.run(self.llm, sections)
                meth_out = await stage3_methodologist.run(self.llm, sections)
                comm_out = await stage4_communication.run(self.llm, sections)
                logger.info(
                    "[%s] Stages 2-4 complete (%s) — DE scores=%s  METH scores=%s  COMM scores=%s",
                    job_id,
                    _elapsed(t),
                    {k: v.get("score") for k, v in de_out.get("scores", {}).items()},
                    {k: v.get("score") for k, v in meth_out.get("scores", {}).items()},
                    {k: v.get("score") for k, v in comm_out.get("scores", {}).items()},
                )
                await session_service.update_version(db, version_id, stage="auditing", progress=40)

                # ----------------------------------------------------------------
                # Stage 5: Self-critique (sequential audits)
                # ----------------------------------------------------------------
                t = time.perf_counter()
                logger.info("[%s] Stage 5 (self-critique audits) — starting", job_id)
                de_audit = await stage5_self_critique.run(self.llm, "Domain Expert", de_out)
                meth_audit = await stage5_self_critique.run(self.llm, "Methodologist", meth_out)
                comm_audit = await stage5_self_critique.run(self.llm, "Communication Specialist", comm_out)
                logger.info(
                    "[%s] Stage 5 complete (%s) — DE quality=%s  METH quality=%s  COMM quality=%s",
                    job_id,
                    _elapsed(t),
                    de_audit.get("overall_quality"),
                    meth_audit.get("overall_quality"),
                    comm_audit.get("overall_quality"),
                )
                for audit in (de_audit, meth_audit, comm_audit):
                    issues = audit.get("issues", [])
                    if issues:
                        logger.debug(
                            "[%s]   %s audit issues: %s",
                            job_id,
                            audit.get("reviewer_name"),
                            [i.get("type") for i in issues],
                        )
                await session_service.update_version(db, version_id, stage="reflecting", progress=55)

                # ----------------------------------------------------------------
                # Stage 6: Reflection (sequential reflections)
                # ----------------------------------------------------------------
                t = time.perf_counter()
                logger.info("[%s] Stage 6 (reflection pass) — starting", job_id)
                de_final = await stage6_reflection.run(self.llm, "Domain Expert", de_out, de_audit, sections)
                meth_final = await stage6_reflection.run(self.llm, "Methodologist", meth_out, meth_audit, sections)
                comm_final = await stage6_reflection.run(self.llm, "Communication Specialist", comm_out, comm_audit, sections)
                logger.info(
                    "[%s] Stage 6 complete (%s) — DE final=%s  METH final=%s  COMM final=%s",
                    job_id,
                    _elapsed(t),
                    {k: v.get("score") for k, v in de_final.get("final_scores", {}).items()},
                    {k: v.get("score") for k, v in meth_final.get("final_scores", {}).items()},
                    {k: v.get("score") for k, v in comm_final.get("final_scores", {}).items()},
                )
                await session_service.update_version(db, version_id, stage="consensus", progress=68)

                # ----------------------------------------------------------------
                # Stage 7: Consensus
                # ----------------------------------------------------------------
                t = time.perf_counter()
                logger.info("[%s] Stage 7 (consensus reconciliation) — starting", job_id)
                consensus_out = await stage7_consensus.run(
                    self.llm, de_final, meth_final, comm_final, document_text
                )
                logger.info(
                    "[%s] Stage 7 complete (%s) — scores=%s  deferral=%s",
                    job_id,
                    _elapsed(t),
                    {k: v.get("score") for k, v in consensus_out.get("scores", {}).items()},
                    consensus_out.get("deferral_assessment", {}).get("recommendation"),
                )
                await session_service.update_version(db, version_id, stage="scoring", progress=75)

                # ----------------------------------------------------------------
                # Stage 8: Scoring (pure Python, no LLM)
                # ----------------------------------------------------------------
                t = time.perf_counter()
                logger.info("[%s] Stage 8 (deterministic scoring) — starting", job_id)
                scoring_result = stage8_scoring.run(consensus_out)
                logger.info(
                    "[%s] Stage 8 complete (%s) — final_score=%s  grade=%s  "
                    "gate=%s  deferred=%s  uncertainty_band=%s",
                    job_id,
                    _elapsed(t),
                    scoring_result.get("final_score"),
                    scoring_result.get("grade_band"),
                    scoring_result.get("gate_triggered"),
                    scoring_result.get("deferred"),
                    scoring_result.get("uncertainty_band"),
                )
                await session_service.update_version(db, version_id, stage="feedback", progress=82)

                # ----------------------------------------------------------------
                # Stage 9: Feedback synthesis
                # ----------------------------------------------------------------
                t = time.perf_counter()
                logger.info("[%s] Stage 9 (feedback synthesis) — starting", job_id)
                feedback_out = await stage9_feedback.run(
                    self.llm, consensus_out, scoring_result, sections
                )
                # Enrich citations with page numbers from the original document
                if pages:
                    for item in feedback_out.get("strengths", []):
                        if isinstance(item, dict):
                            for cit in item.get("citations", []):
                                if cit.get("quote") and cit.get("page") is None:
                                    cit["page"] = self.doc_service.find_quote_page(pages, cit["quote"])
                    for item in feedback_out.get("areas_for_improvement", []):
                        if isinstance(item, dict):
                            for cit in item.get("citations", []):
                                if cit.get("quote") and cit.get("page") is None:
                                    cit["page"] = self.doc_service.find_quote_page(pages, cit["quote"])
                logger.info(
                    "[%s] Stage 9 complete (%s) — strengths=%d  improvements=%d",
                    job_id,
                    _elapsed(t),
                    len(feedback_out.get("strengths", [])),
                    len(feedback_out.get("areas_for_improvement", [])),
                )
                await session_service.update_version(db, version_id, stage="verification", progress=92)

                # ----------------------------------------------------------------
                # Stage 10: Verification guard
                # ----------------------------------------------------------------
                t = time.perf_counter()
                logger.info("[%s] Stage 10 (verification guard) — starting", job_id)
                verification_out = await stage10_verification.run(
                    self.llm, feedback_out, document_text, injection_scan
                )
                logger.info(
                    "[%s] Stage 10 complete (%s) — integrity=%s  recommendation=%s  injection=%s",
                    job_id,
                    _elapsed(t),
                    verification_out.get("overall_integrity"),
                    verification_out.get("final_recommendation"),
                    verification_out.get("injection_found"),
                )
                if verification_out.get("injection_found"):
                    logger.warning(
                        "[%s] INJECTION DETECTED — patterns: %s",
                        job_id,
                        [p.get("type") for p in verification_out.get("detected_patterns", [])],
                    )
                await session_service.update_version(db, version_id, stage="complete", progress=100)

                # ----------------------------------------------------------------
                # Assemble final result
                # ----------------------------------------------------------------
                result = EvaluationResult(
                    job_id=job_id,
                    status="complete",
                    scoring=scoring_result,
                    feedback=feedback_out,
                    verification=verification_out,
                    consensus={
                        "scores": consensus_out.get("scores", {}),
                        "deferral_assessment": consensus_out.get("deferral_assessment", {}),
                        "complete": consensus_out.get("complete", False),
                        "integrity_flags": consensus_out.get("integrity_flags", []),
                        "validation_errors": consensus_out.get("validation_errors", []),
                    },
                    pipeline_metadata={
                        "sections_found": len(sections),
                        "gate_triggered": scoring_result.get("gate_triggered", False),
                        "deferred": scoring_result.get("deferred", False),
                        "scoring_complete": scoring_result.get("scoring_complete", False),
                        "deferral_reasons": scoring_result.get("deferral_reasons", []),
                        "integrity": verification_out.get("overall_integrity", "PASS"),
                        "final_recommendation": verification_out.get("final_recommendation", "RELEASE"),
                        "injection_found": verification_out.get("injection_found", False),
                    },
                )
                await session_service.set_version_result(db, version_id, result)

                total = _elapsed(pipeline_start)
                logger.info(
                    "[%s] Pipeline COMPLETE — total_time=%s  score=%s  grade=%s",
                    job_id,
                    total,
                    scoring_result.get("final_score"),
                    scoring_result.get("grade_band"),
                )
                return result

            except Exception as exc:
                logger.exception(
                    "[%s] Pipeline FAILED — elapsed=%s  error=%s",
                    job_id,
                    _elapsed(pipeline_start),
                    exc,
                )
                if mark_failed:
                    await session_service.set_version_failed(db, version_id, str(exc))
                raise
