# Graph Report - AI-Evaluation-Work  (2026-07-24)

## Corpus Check
- 97 files · ~36,043 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 664 nodes · 1118 edges · 78 communities (51 shown, 27 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0a8e1751`
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
- session_service.py
- ResultWorkspace.jsx
- Engineering Report Evaluation API
- stage9_feedback.py
- parse_xml_response
- api.js
- RunningEvaluation.jsx
- stage10_verification.py
- LLMService
- Part 4 — Reviewer Transparency and Complete Comparison Workspace
- SessionsDrawer.jsx
- stage6_reflection.py
- Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications
- ASSESSMENT_WORKSPACE_REDESIGN_ROADMAP.md
- AppShell.jsx
- TopBar.jsx
- Part 1 — Complete Frontend Replacement and Core Evaluation Experience
- DocumentPreview.jsx
- Engineering Report Evaluation — Frontend
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `LLMService` - 29 edges
2. `parse_xml_response()` - 28 edges
3. `get_settings()` - 21 edges
4. `scan_document()` - 21 edges
5. `compute_score()` - 19 edges
6. `format_sections_for_prompt()` - 14 edges
7. `DocumentService` - 13 edges
8. `Part 8 — Accounts, Roles, Security, Backup, Diagnostics, and Production Readiness` - 13 edges
9. `extract_scores_from_review()` - 12 edges
10. `handleResponse()` - 12 edges

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

## Communities (78 total, 27 thin omitted)

### Community 0 - "App Config & Logging"
Cohesion: 0.15
Nodes (20): Config, get_settings(), Settings, compute_median_scores(), format_sections_for_prompt(), Any, Shared pipeline utilities: section formatting and self-consistency scoring., Format parsed sections into a prompt-ready string, truncating to MAX_SECTION_CHA (+12 more)

### Community 1 - "Verification & Feedback Stages"
Cohesion: 0.18
Nodes (11): 10. Responsive and accessible completion, 1. New application shell, 2. Design system, 3. Theme system — complete the half-built work, 4. Redesigned new-evaluation experience, 5. Redesigned running-evaluation experience, 6. Redesigned result workspace, 7. Complete the charts and status visualisations (+3 more)

### Community 2 - "Scoring Engine"
Cohesion: 0.08
Nodes (33): compute_score(), _grade_band(), Any, Deterministic, policy-based scoring for the document evaluation pipeline., Entry point for the orchestrator., Return a rubric level only when it is a whole number on the 0--4 scale., Map the 0--100 scale to bands consistent with the 0--4 rubric labels., Calculate achievement, confidence risk, gates, and moderation flags.      F1  No (+25 more)

### Community 3 - "Frontend UI Components"
Cohesion: 0.09
Nodes (21): CriteriaRadar(), ORDER, COLUMNS, CONFIDENCE_RANK, CRITERION_ORDER, CriterionTable(), MetadataPanel(), CriterionCallout() (+13 more)

### Community 4 - "System Architecture Overview"
Cohesion: 0.22
Nodes (9): FastAPI, google-genai SDK, httpx (Async HTTP Client), Pydantic v2, PyMuPDF (PDF Parsing), pytest-asyncio (Async Test Support), python-docx (DOCX Parsing), Python Dependencies (requirements.txt) (+1 more)

### Community 5 - "Frontend API Client"
Cohesion: 0.20
Nodes (10): SubmitForm(), EmptyState(), TopBarDispatchContext, TopBarProvider(), TopBarValueContext, useTopBarConfig(), useTopBarDispatch(), Dashboard() (+2 more)

### Community 6 - "Segmentation & Critique Stages"
Cohesion: 0.17
Nodes (24): _char_script(), DetectedPattern, _location(), Deterministic document-attack scanner.  This intentionally is NOT an LLM prompt., Scan raw, untrusted document text for known attack patterns. Pure function, no I, RiskLevel, _scan_base64_blobs(), scan_document() (+16 more)

### Community 7 - "Part 4 — Batch Grading, Analytics, Auth & Hardening"
Cohesion: 0.10
Nodes (20): Accounts and roles, API tokens, Audit trail, Backup and restore, Definition of complete for every part, Dependencies, Diagnostics and operations, Done when (+12 more)

### Community 8 - "Frontend Build Dependencies"
Cohesion: 0.09
Nodes (21): dependencies, docx, html2pdf.js, pdfjs-dist, react, react-dom, react-is, react-router-dom (+13 more)

### Community 10 - "Async Job Store"
Cohesion: 0.22
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
Cohesion: 0.13
Nodes (29): get_db(), FastAPI dependency — one session per request., Centralised logging configuration.  Call setup_logging() once at application sta, setup_logging(), delete_session(), document_file(), document_html(), document_meta() (+21 more)

### Community 24 - "Engineering Report Evaluation API"
Cohesion: 0.17
Nodes (12): Batch ingestion, Cohort analytics, Cohorts, Dependencies, Done when, Estimated effort, Exports, Outcome (+4 more)

### Community 25 - "DocumentService"
Cohesion: 0.11
Nodes (13): CriterionScore, EvaluationResult, PipelineStatus, BaseModel, ScoringResult, _elapsed(), PipelineOrchestrator, UUID (+5 more)

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

### Community 55 - "session_service.py"
Cohesion: 0.14
Nodes (32): do_run_migrations(), Run migrations in 'offline' mode., Run migrations in 'online' mode using an async engine., run_migrations_offline(), run_migrations_online(), Base, Document, EvaluationVersion (+24 more)

### Community 56 - "ResultWorkspace.jsx"
Cohesion: 0.14
Nodes (11): FeedbackPanel(), TabPanel(), Tabs(), VerificationPanel(), buildDocx(), CRITERION_ORDER, criterionRows(), downloadBlob() (+3 more)

### Community 57 - "Engineering Report Evaluation API"
Cohesion: 0.11
Nodes (17): API Endpoints, Configuration, Engineering Report Evaluation API, Environment variables, Frontend, `GET /api/v1/health`, `GET /api/v1/result/{job_id}`, `GET /api/v1/status/{job_id}` (+9 more)

### Community 58 - "stage9_feedback.py"
Cohesion: 0.23
Nodes (14): _extract_block(), _extract_citations(), _extract_point_text(), _extract_points(), Any, Stage 9: Feedback Synthesis  Input:  llm (LLMService),         consensus_out  (D, Best-effort recovery when the LLM's XML is too malformed to parse even     after, Synthesise written feedback from consensus evaluation and scoring. (+6 more)

### Community 59 - "parse_xml_response"
Cohesion: 0.18
Nodes (13): Any, Run methodologist review with self-consistency sampling., run(), extract_scores_from_review(), _fix_ampersands(), parse_xml_response(), Any, LLM output frequently embeds verbatim document text inside attribute     values (+5 more)

### Community 60 - "api.js"
Cohesion: 0.27
Nodes (13): archiveSession(), evaluateSync(), getDocumentMeta(), getResult(), getSession(), getStatus(), handleResponse(), health() (+5 more)

### Community 61 - "RunningEvaluation.jsx"
Cohesion: 0.20
Nodes (5): getStepState(), ProgressTracker(), STAGES, ErrorBoundary, FailureScreen()

### Community 62 - "stage10_verification.py"
Cohesion: 0.25
Nodes (8): _combine(), Any, Stage 10: Verification Guard  Input:  llm (LLMService),         feedback_out, Deterministically merge the factual verdict with the security scan.     Whicheve, Run factual verification and combine it with the security scan., run(), Prompt for Stage 10: Factual Verification.  This stage's LLM prompt covers factu, ScanResult

### Community 63 - "LLMService"
Cohesion: 0.24
Nodes (8): _empty_audit(), Any, Stage 5: Self-Critique Audit  Input:  llm (LLMService), reviewer_name (str), rev, Audit reviewer output for quality issues., run(), Prompt for Stage 5: Self-Critique Audit.  Contract with app/pipeline/stage5_self, LLMService, OpenRouter-backed LLM client used by every pipeline stage.

### Community 64 - "Part 4 — Reviewer Transparency and Complete Comparison Workspace"
Cohesion: 0.18
Nodes (11): APIs, Comparison modes, Comparison UI, Dependencies, Done when, Estimated effort, Outcome, Part 4 — Reviewer Transparency and Complete Comparison Workspace (+3 more)

### Community 65 - "SessionsDrawer.jsx"
Cohesion: 0.29
Nodes (8): listSessions(), App(), formatWhen(), SessionsDrawer(), statusBadgeClass(), ToastContext, ToastProvider(), useToast()

### Community 66 - "stage6_reflection.py"
Cohesion: 0.29
Nodes (8): _fallback_result(), _parse_final_scores(), Any, Stage 6: Reflection Pass  Input:  llm (LLMService), reviewer_name (str),, Extract criterion scores from <final_scores> block., Reviewer revisits evaluation in light of audit feedback., run(), Prompt for Stage 6: Reflection Pass.  Contract with app/pipeline/stage6_reflecti

### Community 67 - "Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications"
Cohesion: 0.20
Nodes (10): Backend, Dependencies, Done when, Estimated effort, Failure behaviour, Frontend, Outcome, Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications (+2 more)

### Community 68 - "ASSESSMENT_WORKSPACE_REDESIGN_ROADMAP.md"
Cohesion: 0.22
Nodes (8): Backend, Current baseline, Engineering Assessment Workspace — Complete Redesign Roadmap, Frontend, Half-completed frontend features that must not be forgotten, Meaning of “independent” in this roadmap, Non-negotiable execution rules, Product direction

### Community 69 - "AppShell.jsx"
Cohesion: 0.39
Nodes (5): AppShell(), initialCollapsed(), MobileDrawer(), NAV_ITEMS, Sidebar()

### Community 70 - "TopBar.jsx"
Cohesion: 0.36
Nodes (7): TopBar(), useTopBar(), preferredTheme(), ThemeContext, ThemeProvider(), THEMES, useTheme()

### Community 71 - "Part 1 — Complete Frontend Replacement and Core Evaluation Experience"
Cohesion: 0.25
Nodes (8): Backend work, Dependencies, Done when, Estimated effort, Outcome, Part 1 — Complete Frontend Replacement and Core Evaluation Experience, Verification, Why this is a complete part

### Community 72 - "DocumentPreview.jsx"
Cohesion: 0.39
Nodes (7): getDocumentBlob(), getDocumentHtml(), clearAllHighlights(), DocumentPreview(), drawHighlights(), findItemsForQuote(), scrollIntoContainer()

### Community 73 - "Engineering Report Evaluation — Frontend"
Cohesion: 0.33
Nodes (5): Build for production, Engineering Report Evaluation — Frontend, Environment variables, Getting started, Prerequisites

## Knowledge Gaps
- **178 isolated node(s):** `Config`, `name`, `private`, `version`, `type` (+173 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMService` connect `LLMService` to `App Config & Logging`, `stage6_reflection.py`, `Async Job Store`, `Consensus Reconciliation Stage`, `stage7_consensus.py`, `DocumentService`, `stage9_feedback.py`, `parse_xml_response`, `stage10_verification.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `App Config & Logging` to `Scoring Engine`, `session_service.py`, `evaluation.py`, `parse_xml_response`, `LLMService`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `parse_xml_response()` connect `parse_xml_response` to `App Config & Logging`, `stage6_reflection.py`, `Scoring Engine`, `stage7_consensus.py`, `stage9_feedback.py`, `stage10_verification.py`, `LLMService`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `Run migrations in 'offline' mode.`, `Run migrations in 'online' mode using an async engine.`, `Config` to the rest of the system?**
  _254 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App Config & Logging` be split into smaller, more focused modules?**
  _Cohesion score 0.1455026455026455 - nodes in this community are weakly interconnected._
- **Should `Scoring Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.07676767676767676 - nodes in this community are weakly interconnected._
- **Should `Frontend UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.0944741532976827 - nodes in this community are weakly interconnected._