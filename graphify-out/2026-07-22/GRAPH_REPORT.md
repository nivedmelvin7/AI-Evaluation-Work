# Graph Report - AI-Evaluation-Work  (2026-07-17)

## Corpus Check
- 56 files · ~20,827 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 387 nodes · 594 edges · 51 communities (24 shown, 27 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `275b787f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- App Config & Logging
- Verification & Feedback Stages
- Scoring Engine
- Frontend UI Components
- System Architecture Overview
- Frontend API Client
- Segmentation & Critique Stages
- Part 4 — Batch Grading, Analytics, Auth & Hardening
- Frontend Build Dependencies
- Pipeline Concepts & Scoring Rules
- Async Job Store
- Consensus Reconciliation Stage
- stage7_consensus.py
- Request Models
- Graphify Instructions
- evaluation.py
- Engineering Report Evaluation API
- DocumentService
- Engineering Report Evaluation — Frontend
- CLAUDE.md
- frontend/index.html (SPA Entry Point)
- React SPA Frontend
- POST /api/v1/evaluate (Async)
- EvaluationResult
- Google Gemini LLM Backend
- GET /api/v1/health
- Multi-Agent Evaluation Pipeline
- GET /api/v1/result/{job_id}
- Scoring Formulas F1-F9
- Self-Consistency (Parallel Runs)
- Stage 10: Verification Guard
- Stage 1: Segmentation
- Stage 2: Domain Expert Reviewer
- Stage 3: Methodologist Reviewer
- Stage 4: Communication Specialist Reviewer
- Stage 5: Self-Critique
- Stage 6: Reflection
- Stage 7: Consensus
- Stage 8: Scoring (Pure Python, F1-F9)
- Stage 9: Feedback Synthesis
- GET /api/v1/status/{job_id}
- POST /api/v1/evaluate/sync (Protected)
- run.sh

## God Nodes (most connected - your core abstractions)
1. `parse_xml_response()` - 28 edges
2. `LLMService` - 25 edges
3. `compute_score()` - 20 edges
4. `get_settings()` - 19 edges
5. `format_sections_for_prompt()` - 14 edges
6. `DocumentService` - 13 edges
7. `_make_scores()` - 13 edges
8. `extract_scores_from_review()` - 12 edges
9. `Engineering Report Evaluation API` - 10 edges
10. `compute_median_scores()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `test_full_marks()` --calls--> `compute_score()`  [EXTRACTED]
  tests/test_pipeline.py → app/pipeline/stage8_scoring.py
- `test_gate_caps_at_49()` --calls--> `compute_score()`  [EXTRACTED]
  tests/test_pipeline.py → app/pipeline/stage8_scoring.py
- `test_extract_scores_handles_unchanged_format()` --calls--> `parse_xml_response()`  [EXTRACTED]
  tests/test_pipeline.py → app/utils/xml_parser.py
- `test_xml_parser_malformed_ampersand()` --calls--> `parse_xml_response()`  [EXTRACTED]
  tests/test_pipeline.py → app/utils/xml_parser.py
- `test_xml_parser_returns_none_on_garbage()` --calls--> `parse_xml_response()`  [EXTRACTED]
  tests/test_pipeline.py → app/utils/xml_parser.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Format Document Parsing Stack** — requirements_pymupdf, requirements_python_docx, readme_stage1_segmentation [INFERRED 0.85]

## Communities (51 total, 27 thin omitted)

### Community 0 - "App Config & Logging"
Cohesion: 0.06
Nodes (43): compute_median_scores(), format_sections_for_prompt(), Any, Format parsed sections into a prompt-ready string, truncating to MAX_SECTION_CHA, Given N runs of reviewer scores, return the median score per criterion     with, Any, Stage 2: Domain Expert Reviewer  Input:  llm (LLMService), sections (List[Dict]), Run domain expert review with self-consistency sampling. (+35 more)

### Community 1 - "Verification & Feedback Stages"
Cohesion: 0.33
Nodes (11): _extract_block(), _extract_citations(), _extract_point_text(), _extract_points(), Any, Stage 9: Feedback Synthesis  Input:  llm (LLMService),         consensus_out  (D, Synthesise written feedback from consensus evaluation and scoring., Best-effort recovery when the LLM's XML is too malformed to parse even     after (+3 more)

### Community 2 - "Scoring Engine"
Cohesion: 0.10
Nodes (33): compute_score(), Any, Stage 8: Deterministic Scoring  Input:  consensus_out (Dict from stage 7) Output, Entry point for the orchestrator. Extracts scores and runs compute_score., Apply formulas F1 through F9.      F1  Normalise:        s_i = level_i / 4     F, run(), _make_scores(), Tests for stage8_scoring deterministic formulas. (+25 more)

### Community 3 - "Frontend UI Components"
Cohesion: 0.12
Nodes (10): CRITERION_ORDER, CriterionTable(), FeedbackPanel(), MetadataPanel(), downloadJson(), ResultView(), gradeMeta(), ScoreCard() (+2 more)

### Community 4 - "System Architecture Overview"
Cohesion: 0.22
Nodes (9): FastAPI, google-genai SDK, httpx (Async HTTP Client), Pydantic v2, PyMuPDF (PDF Parsing), pytest-asyncio (Async Test Support), python-docx (DOCX Parsing), Python Dependencies (requirements.txt) (+1 more)

### Community 5 - "Frontend API Client"
Cohesion: 0.13
Nodes (20): evaluateSync(), getDocumentBlob(), getDocumentHtml(), getDocumentMeta(), getResult(), getStatus(), handleResponse(), health() (+12 more)

### Community 7 - "Part 4 — Batch Grading, Analytics, Auth & Hardening"
Cohesion: 0.07
Nodes (27): Appendix A — Reusable asset inventory (copy-paste, minimal rewrite), Appendix B — Explicitly out of scope (odysseus features that don't fit a report grader), Appendix C — Decisions to confirm before executing a part, Assumptions (override any of these and I'll adjust the plan), Backend work (this repo), Backend work (this repo), Backend work (this repo), Done when (+19 more)

### Community 8 - "Frontend Build Dependencies"
Cohesion: 0.12
Nodes (15): dependencies, pdfjs-dist, react, react-dom, devDependencies, vite, @vitejs/plugin-react, name (+7 more)

### Community 10 - "Async Job Store"
Cohesion: 0.24
Nodes (3): JobStore, Any, Thread-safe in-memory job store.     For production, replace _store and _results

### Community 11 - "Consensus Reconciliation Stage"
Cohesion: 0.13
Nodes (19): _default_verification(), Any, Stage 10: Verification Guard  Input:  llm (LLMService),         feedback_out, Run factual verification and injection detection on the feedback., run(), _fallback_section(), Any, Stage 1: Document Segmentation  Input:  llm (LLMService), document_text (str) Ou (+11 more)

### Community 12 - "stage7_consensus.py"
Cohesion: 0.39
Nodes (8): _build_consensus_prompt(), _fallback_consensus(), _format_reviewer_scores(), Any, Stage 7: Consensus Reconciliation  Input:  llm (LLMService),         de_final, Reconcile post-reflection reviewer scores into a single consensus., Build a simple fallback consensus from available reviewer scores., run()

### Community 13 - "Request Models"
Cohesion: 0.67
Nodes (3): EvaluationStatusResponse, BaseModel, TextEvaluationRequest

### Community 23 - "evaluation.py"
Cohesion: 0.11
Nodes (17): Config, get_settings(), Settings, Centralised logging configuration.  Call setup_logging() once at application sta, setup_logging(), Shared pipeline utilities: section formatting and self-consistency scoring., evaluate(), evaluate_sync() (+9 more)

### Community 24 - "Engineering Report Evaluation API"
Cohesion: 0.11
Nodes (17): API Endpoints, Configuration, Engineering Report Evaluation API, Environment variables, Frontend, `GET /api/v1/health`, `GET /api/v1/result/{job_id}`, `GET /api/v1/status/{job_id}` (+9 more)

### Community 25 - "DocumentService"
Cohesion: 0.12
Nodes (13): CriterionScore, EvaluationResult, PipelineStatus, BaseModel, ScoringResult, _elapsed(), PipelineOrchestrator, Pipeline orchestrator. Runs all 10 stages in sequence. (+5 more)

### Community 26 - "Engineering Report Evaluation — Frontend"
Cohesion: 0.33
Nodes (5): Build for production, Engineering Report Evaluation — Frontend, Environment variables, Getting started, Prerequisites

## Knowledge Gaps
- **86 isolated node(s):** `Config`, `name`, `private`, `version`, `type` (+81 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `compute_score()` connect `Scoring Engine` to `App Config & Logging`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `parse_xml_response()` connect `App Config & Logging` to `Verification & Feedback Stages`, `Consensus Reconciliation Stage`, `stage7_consensus.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `evaluation.py` to `App Config & Logging`, `Consensus Reconciliation Stage`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **What connects `Config`, `Centralised logging configuration.  Call setup_logging() once at application sta`, `Shared pipeline utilities: section formatting and self-consistency scoring.` to the rest of the system?**
  _145 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App Config & Logging` be split into smaller, more focused modules?**
  _Cohesion score 0.060451977401129946 - nodes in this community are weakly interconnected._
- **Should `Scoring Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.10084033613445378 - nodes in this community are weakly interconnected._
- **Should `Frontend UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._