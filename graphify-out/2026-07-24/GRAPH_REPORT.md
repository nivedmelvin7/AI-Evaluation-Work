# Graph Report - AI-Evaluation-Work  (2026-07-22)

## Corpus Check
- 90 files · ~33,588 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 600 nodes · 962 edges · 55 communities (29 shown, 26 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3e387d5e`
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
- Part 5 — Improve, Version, Re-evaluate, and Measure Progress
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
- rubric_backbone.py
- run.sh
- AGENTS.md

## God Nodes (most connected - your core abstractions)
1. `LLMService` - 29 edges
2. `parse_xml_response()` - 28 edges
3. `scan_document()` - 21 edges
4. `get_settings()` - 19 edges
5. `compute_score()` - 19 edges
6. `format_sections_for_prompt()` - 14 edges
7. `DocumentService` - 13 edges
8. `Part 8 — Accounts, Roles, Security, Backup, Diagnostics, and Production Readiness` - 13 edges
9. `extract_scores_from_review()` - 12 edges
10. `humanizeCriterion()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_extract_scores_handles_unchanged_format()` --calls--> `parse_xml_response()`  [EXTRACTED]
  tests/test_pipeline.py → app/utils/xml_parser.py
- `test_xml_parser_malformed_ampersand()` --calls--> `parse_xml_response()`  [EXTRACTED]
  tests/test_pipeline.py → app/utils/xml_parser.py
- `test_xml_parser_returns_none_on_garbage()` --calls--> `parse_xml_response()`  [EXTRACTED]
  tests/test_pipeline.py → app/utils/xml_parser.py
- `test_xml_parser_well_formed()` --calls--> `parse_xml_response()`  [EXTRACTED]
  tests/test_pipeline.py → app/utils/xml_parser.py
- `test_xml_parser_with_markdown_fences()` --calls--> `parse_xml_response()`  [EXTRACTED]
  tests/test_pipeline.py → app/utils/xml_parser.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Format Document Parsing Stack** — requirements_pymupdf, requirements_python_docx, readme_stage1_segmentation [INFERRED 0.85]

## Communities (55 total, 26 thin omitted)

### Community 0 - "App Config & Logging"
Cohesion: 0.05
Nodes (65): Config, get_settings(), Settings, compute_median_scores(), format_sections_for_prompt(), Any, Shared pipeline utilities: section formatting and self-consistency scoring., Format parsed sections into a prompt-ready string, truncating to MAX_SECTION_CHA (+57 more)

### Community 1 - "Verification & Feedback Stages"
Cohesion: 0.04
Nodes (48): 10. Responsive and accessible completion, 1. New application shell, 2. Design system, 3. Theme system — complete the half-built work, 4. Redesigned new-evaluation experience, 5. Redesigned running-evaluation experience, 6. Redesigned result workspace, 7. Complete the charts and status visualisations (+40 more)

### Community 2 - "Scoring Engine"
Cohesion: 0.08
Nodes (33): compute_score(), _grade_band(), Any, Deterministic, policy-based scoring for the document evaluation pipeline., Entry point for the orchestrator., Return a rubric level only when it is a whole number on the 0--4 scale., Map the 0--100 scale to bands consistent with the 0--4 rubric labels., Calculate achievement, confidence risk, gates, and moderation flags.      F1  No (+25 more)

### Community 3 - "Frontend UI Components"
Cohesion: 0.06
Nodes (32): CriteriaRadar(), ORDER, COLUMNS, CONFIDENCE_RANK, CRITERION_ORDER, CriterionTable(), FeedbackPanel(), MetadataPanel() (+24 more)

### Community 4 - "System Architecture Overview"
Cohesion: 0.22
Nodes (9): FastAPI, google-genai SDK, httpx (Async HTTP Client), Pydantic v2, PyMuPDF (PDF Parsing), pytest-asyncio (Async Test Support), python-docx (DOCX Parsing), Python Dependencies (requirements.txt) (+1 more)

### Community 5 - "Frontend API Client"
Cohesion: 0.06
Nodes (47): evaluateSync(), getDocumentBlob(), getDocumentHtml(), getDocumentMeta(), getResult(), getStatus(), handleResponse(), health() (+39 more)

### Community 6 - "Segmentation & Critique Stages"
Cohesion: 0.12
Nodes (30): _combine(), Any, Deterministically merge the factual verdict with the security scan.     Whicheve, Run factual verification and combine it with the security scan., run(), _char_script(), DetectedPattern, _location() (+22 more)

### Community 7 - "Part 4 — Batch Grading, Analytics, Auth & Hardening"
Cohesion: 0.10
Nodes (20): Accounts and roles, API tokens, Audit trail, Backup and restore, Definition of complete for every part, Dependencies, Diagnostics and operations, Done when (+12 more)

### Community 8 - "Frontend Build Dependencies"
Cohesion: 0.06
Nodes (33): Document parsing service. Supports: .pdf (PyMuPDF), .docx (python-docx), .txt (, docx, dependencies, docx, html2pdf.js, pdfjs-dist, react, react-dom (+25 more)

### Community 10 - "Async Job Store"
Cohesion: 0.26
Nodes (14): LLMError, Exception, _make_service(), _mock_response(), Any, Tests for LLMService (OpenRouter is the sole LLM provider).  These mock the HTTP, The app must still boot even with no OpenRouter key configured —     the error s, test_all_retries_exhausted_raises_llm_error() (+6 more)

### Community 11 - "Consensus Reconciliation Stage"
Cohesion: 0.19
Nodes (14): _fallback_section(), _find_snippet(), _normalise_ws(), _parse_markers(), Any, Stage 1: Document Segmentation  Input:  llm (LLMService), document_text (str) Ou, Turn boundary markers into full sections by slicing the original text., Return the entire document as one section when segmentation fails. (+6 more)

### Community 12 - "stage7_consensus.py"
Cohesion: 0.29
Nodes (9): _build_consensus_prompt(), _fallback_consensus(), _format_reviewer_scores(), Any, Stage 7: Consensus Reconciliation  Input:  llm (LLMService),         de_final, Reconcile post-reflection reviewer scores into a single consensus., Build a simple fallback consensus from available reviewer scores., run() (+1 more)

### Community 13 - "Request Models"
Cohesion: 0.67
Nodes (3): EvaluationStatusResponse, BaseModel, TextEvaluationRequest

### Community 23 - "evaluation.py"
Cohesion: 0.06
Nodes (15): Centralised logging configuration.  Call setup_logging() once at application s, setup_logging(), evaluate(), evaluate_sync(), health(), REST API routes for the evaluation pipeline.  POST /api/v1/evaluate          —, Returns (text, pages, file_bytes, content_type, filename).     pages is None wh, _resolve_text_and_meta() (+7 more)

### Community 24 - "Engineering Report Evaluation API"
Cohesion: 0.17
Nodes (12): Batch ingestion, Cohort analytics, Cohorts, Dependencies, Done when, Estimated effort, Exports, Outcome (+4 more)

### Community 25 - "DocumentService"
Cohesion: 0.13
Nodes (11): CriterionScore, EvaluationResult, PipelineStatus, BaseModel, ScoringResult, _elapsed(), PipelineOrchestrator, DocumentService (+3 more)

### Community 26 - "Engineering Report Evaluation — Frontend"
Cohesion: 0.18
Nodes (11): APIs, Backend and data, Dependencies, Done when, Estimated effort, Frontend, Outcome, Part 2 — Durable Storage and Complete Evaluation Library (+3 more)

### Community 27 - "Part 5 — Improve, Version, Re-evaluate, and Measure Progress"
Cohesion: 0.18
Nodes (11): Data model and backend, Dependencies, Done when, Estimated effort, Feedback anchoring, Improve workspace, Outcome, Part 5 — Improve, Version, Re-evaluate, and Measure Progress (+3 more)

### Community 28 - "CLAUDE.md"
Cohesion: 0.18
Nodes (11): Dependencies, Done when, Estimated effort, Frontend, Outcome, Part 6 — Versioned Rubrics and Evaluation Profiles, Profile contents, Scope (+3 more)

### Community 51 - "rubric_backbone.py"
Cohesion: 0.29
Nodes (3): Prompt for Stage 2: Domain Expert Reviewer.  Contract with app/pipeline/stage2_d, Prompt for Stage 3: Methodologist Reviewer.  Contract with app/pipeline/stage3_m, Prompt for Stage 4: Communication Specialist Reviewer.  Contract with app/pipeli

## Knowledge Gaps
- **157 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+152 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `name`, `private`, `version` to the rest of the system?**
  _157 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App Config & Logging` be split into smaller, more focused modules?**
  _Cohesion score 0.052100840336134456 - nodes in this community are weakly interconnected._
- **Should `Verification & Feedback Stages` be split into smaller, more focused modules?**
  _Cohesion score 0.04081632653061224 - nodes in this community are weakly interconnected._
- **Should `Scoring Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.07676767676767676 - nodes in this community are weakly interconnected._
- **Should `Frontend UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.06289308176100629 - nodes in this community are weakly interconnected._
- **Should `Frontend API Client` be split into smaller, more focused modules?**
  _Cohesion score 0.05701592002961866 - nodes in this community are weakly interconnected._
- **Should `Segmentation & Critique Stages` be split into smaller, more focused modules?**
  _Cohesion score 0.12121212121212122 - nodes in this community are weakly interconnected._