"""
Pipeline orchestrator. Runs all 10 stages in sequence.
Stages 2, 3, 4 run in parallel using asyncio.gather.
Stages 5 and 6 run per-reviewer (three times each, also parallel).
"""

import asyncio
import sys
from app.services.llm_service import LLMService
from app.services.document_service import DocumentService
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
from app.utils.job_store import job_store


class PipelineOrchestrator:

    def __init__(self):
        self.llm = LLMService()
        self.doc_service = DocumentService()

    async def run(self, job_id: str, document_text: str) -> EvaluationResult:

        job_store.update(job_id, status="running", stage="segmentation", progress=5)

        try:
            # --- Stage 1: Segmentation ---
            sections = await stage1_segment.run(self.llm, document_text)
            print(f"[{job_id}] Stage 1 complete — {len(sections)} sections found.", file=sys.stderr)
            job_store.update(job_id, stage="reviewing", progress=15)

            # --- Stages 2+3+4: Parallel reviewer pass ---
            de_out, meth_out, comm_out = await asyncio.gather(
                stage2_domain_expert.run(self.llm, sections),
                stage3_methodologist.run(self.llm, sections),
                stage4_communication.run(self.llm, sections),
            )
            print(f"[{job_id}] Stages 2-4 complete.", file=sys.stderr)
            job_store.update(job_id, stage="auditing", progress=40)

            # --- Stage 5: Self-critique (three parallel audits) ---
            de_audit, meth_audit, comm_audit = await asyncio.gather(
                stage5_self_critique.run(self.llm, "Domain Expert", de_out),
                stage5_self_critique.run(self.llm, "Methodologist", meth_out),
                stage5_self_critique.run(self.llm, "Communication Specialist", comm_out),
            )
            print(f"[{job_id}] Stage 5 complete.", file=sys.stderr)
            job_store.update(job_id, stage="reflecting", progress=55)

            # --- Stage 6: Reflection (three parallel reflections) ---
            de_final, meth_final, comm_final = await asyncio.gather(
                stage6_reflection.run(self.llm, "Domain Expert", de_out, de_audit, sections),
                stage6_reflection.run(self.llm, "Methodologist", meth_out, meth_audit, sections),
                stage6_reflection.run(self.llm, "Communication Specialist", comm_out, comm_audit, sections),
            )
            print(f"[{job_id}] Stage 6 complete.", file=sys.stderr)
            job_store.update(job_id, stage="consensus", progress=68)

            # --- Stage 7: Consensus ---
            consensus_out = await stage7_consensus.run(
                self.llm, de_final, meth_final, comm_final
            )
            print(f"[{job_id}] Stage 7 complete.", file=sys.stderr)
            job_store.update(job_id, stage="scoring", progress=75)

            # --- Stage 8: Scoring (pure Python, no LLM) ---
            scoring_result = stage8_scoring.run(consensus_out)
            print(
                f"[{job_id}] Stage 8 complete — score={scoring_result['final_score']}, "
                f"band={scoring_result['grade_band']}.",
                file=sys.stderr,
            )
            job_store.update(job_id, stage="feedback", progress=82)

            # --- Stage 9: Feedback synthesis ---
            feedback_out = await stage9_feedback.run(
                self.llm, consensus_out, scoring_result, sections
            )
            print(f"[{job_id}] Stage 9 complete.", file=sys.stderr)
            job_store.update(job_id, stage="verification", progress=92)

            # --- Stage 10: Verification guard ---
            verification_out = await stage10_verification.run(
                self.llm, feedback_out, document_text
            )
            print(f"[{job_id}] Stage 10 complete — integrity={verification_out.get('overall_integrity')}.", file=sys.stderr)
            job_store.update(job_id, stage="complete", progress=100)

            result = EvaluationResult(
                job_id=job_id,
                status="complete",
                scoring=scoring_result,
                feedback=feedback_out,
                verification=verification_out,
                consensus={
                    "scores": consensus_out.get("scores", {}),
                    "deferral_assessment": consensus_out.get("deferral_assessment", {}),
                },
                pipeline_metadata={
                    "sections_found": len(sections),
                    "gate_triggered": scoring_result.get("gate_triggered", False),
                    "deferred": scoring_result.get("deferred", False),
                    "integrity": verification_out.get("overall_integrity", "PASS"),
                    "final_recommendation": verification_out.get("final_recommendation", "RELEASE"),
                    "injection_found": verification_out.get("injection_found", False),
                },
            )
            job_store.set_result(job_id, result)
            return result

        except Exception as e:
            print(f"[{job_id}] Pipeline failed at stage: {e}", file=sys.stderr)
            job_store.update(job_id, status="failed", error=str(e))
            raise
