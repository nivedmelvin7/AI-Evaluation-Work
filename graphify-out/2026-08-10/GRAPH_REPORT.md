# Graph Report - AI-Evaluation-Work  (2026-07-30)

## Corpus Check
- 98 files · ~37,346 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 686 nodes · 1151 edges · 78 communities (49 shown, 29 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2b3345ae`
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
- ResultWorkspace.jsx
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
9. `Session` - 12 edges
10. `extract_scores_from_review()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_sync_endpoint_blocked_without_key()` --calls--> `get_settings()`  [EXTRACTED]
  tests/test_pipeline.py → app/config.py
- `test_full_marks()` --calls--> `compute_score()`  [EXTRACTED]
  tests/test_pipeline.py → app/pipeline/stage8_scoring.py
- `test_gate_caps_at_49()` --calls--> `compute_score()`  [EXTRACTED]
  tests/test_pipeline.py → app/pipeline/stage8_scoring.py
- `test_base64_blob_is_low_risk_not_rejected()` --calls--> `scan_document()`  [EXTRACTED]
  tests/test_prompt_injection_scanner.py → app/security/prompt_injection_scanner.py
- `test_clean_report_produces_no_false_positive()` --calls--> `scan_document()`  [EXTRACTED]
  tests/test_prompt_injection_scanner.py → app/security/prompt_injection_scanner.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Format Document Parsing Stack** — requirements_pymupdf, requirements_python_docx, readme_stage1_segmentation [INFERRED 0.85]

## Communities (78 total, 29 thin omitted)

### Community 0 - "App Config & Logging"
Cohesion: 0.13
Nodes (19): Config, get_settings(), Settings, compute_median_scores(), Shared pipeline utilities: section formatting and self-consistency scoring., Given N runs of reviewer scores, return the median score per criterion     with, Any, Stage 2: Domain Expert Reviewer  Input:  llm (LLMService), sections (List[Dict]) (+11 more)

### Community 1 - "Verification & Feedback Stages"
Cohesion: 0.11
Nodes (19): 10. Responsive and accessible completion, 1. New application shell, 2. Design system, 3. Theme system — complete the half-built work, 4. Redesigned new-evaluation experience, 5. Redesigned running-evaluation experience, 6. Redesigned result workspace, 7. Complete the charts and status visualisations (+11 more)

### Community 2 - "Scoring Engine"
Cohesion: 0.17
Nodes (22): compute_score(), _grade_band(), Any, Deterministic, policy-based scoring for the document evaluation pipeline., Entry point for the orchestrator., Return a rubric level only when it is a whole number on the 0--4 scale., Map the 0--100 scale to bands consistent with the 0--4 rubric labels., Calculate achievement, confidence risk, gates, and moderation flags.      F1  No (+14 more)

### Community 3 - "Frontend UI Components"
Cohesion: 0.09
Nodes (22): CriteriaRadar(), ORDER, COLUMNS, CONFIDENCE_RANK, CRITERION_ORDER, CriterionTable(), MetadataPanel(), CriterionCallout() (+14 more)

### Community 4 - "System Architecture Overview"
Cohesion: 0.22
Nodes (9): FastAPI, google-genai SDK, httpx (Async HTTP Client), Pydantic v2, PyMuPDF (PDF Parsing), pytest-asyncio (Async Test Support), python-docx (DOCX Parsing), Python Dependencies (requirements.txt) (+1 more)

### Community 5 - "Frontend API Client"
Cohesion: 0.20
Nodes (5): getStepState(), ProgressTracker(), STAGES, ErrorBoundary, FailureScreen()

### Community 6 - "Segmentation & Critique Stages"
Cohesion: 0.11
Nodes (32): _combine(), Any, Stage 10: Verification Guard  Input:  llm (LLMService),         feedback_out, Deterministically merge the factual verdict with the security scan.     Whicheve, Run factual verification and combine it with the security scan., run(), Prompt for Stage 10: Factual Verification.  This stage's LLM prompt covers factu, _char_script() (+24 more)

### Community 7 - "Part 4 — Batch Grading, Analytics, Auth & Hardening"
Cohesion: 0.10
Nodes (20): Accounts and roles, API tokens, Audit trail, Backup and restore, Definition of complete for every part, Dependencies, Diagnostics and operations, Done when (+12 more)

### Community 8 - "Frontend Build Dependencies"
Cohesion: 0.09
Nodes (21): dependencies, docx, html2pdf.js, pdfjs-dist, react, react-dom, react-is, react-router-dom (+13 more)

### Community 10 - "Async Job Store"
Cohesion: 0.19
Nodes (16): LLMError, LLMService, OpenRouter-backed LLM client used by every pipeline stage., Exception, _make_service(), _mock_response(), Any, Tests for LLMService (OpenRouter is the sole LLM provider).  These mock the HTTP (+8 more)

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
Cohesion: 0.16
Nodes (27): get_db(), FastAPI dependency — one session per request., delete_session(), document_file(), document_html(), document_meta(), evaluate(), evaluate_sync() (+19 more)

### Community 24 - "Engineering Report Evaluation API"
Cohesion: 0.33
Nodes (6): Batch ingestion, Cohort analytics, Cohorts, Exports, Scope, Scoreboard and moderation

### Community 25 - "DocumentService"
Cohesion: 0.12
Nodes (14): CriterionScore, EvaluationResult, PipelineStatus, BaseModel, ScoringResult, _elapsed(), PipelineOrchestrator, UUID (+6 more)

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
Cohesion: 0.13
Nodes (36): do_run_migrations(), Run migrations in 'offline' mode., Run migrations in 'online' mode using an async engine., run_migrations_offline(), run_migrations_online(), Base, Document, EvaluationVersion (+28 more)

### Community 56 - "ResultWorkspace.jsx"
Cohesion: 0.33
Nodes (6): Dependencies, Done when, Estimated effort, Outcome, Part 7 — Cohorts, Batch Grading, Moderation, and Cohort Analytics, Why this is a complete part

### Community 57 - "Engineering Report Evaluation API"
Cohesion: 0.07
Nodes (27): API Endpoints, Apply migrations, Configuration, Database, `DELETE /api/v1/sessions/{session_id}`, Document preview, Engineering Report Evaluation API, Environment variables (+19 more)

### Community 58 - "stage9_feedback.py"
Cohesion: 0.23
Nodes (14): _extract_block(), _extract_citations(), _extract_point_text(), _extract_points(), Any, Stage 9: Feedback Synthesis  Input:  llm (LLMService),         consensus_out  (D, Best-effort recovery when the LLM's XML is too malformed to parse even     after, Synthesise written feedback from consensus evaluation and scoring. (+6 more)

### Community 60 - "api.js"
Cohesion: 0.27
Nodes (13): archiveSession(), evaluateSync(), getDocumentMeta(), getResult(), getSession(), getStatus(), handleResponse(), health() (+5 more)

### Community 61 - "RunningEvaluation.jsx"
Cohesion: 0.22
Nodes (9): SubmitForm(), EmptyState(), TopBarDispatchContext, TopBarValueContext, useTopBarConfig(), useTopBarDispatch(), Dashboard(), NewEvaluation() (+1 more)

### Community 62 - "stage10_verification.py"
Cohesion: 0.09
Nodes (21): extract_scores_from_review(), _fix_ampersands(), parse_xml_response(), Any, LLM output frequently embeds verbatim document text inside attribute     values, Extract and parse XML from a raw LLM response.     Returns the root element or N, Extract score and confidence for each criterion from a reviewer XML element., _repair_attribute_values() (+13 more)

### Community 63 - "LLMService"
Cohesion: 0.32
Nodes (6): _empty_audit(), Any, Stage 5: Self-Critique Audit  Input:  llm (LLMService), reviewer_name (str), rev, Audit reviewer output for quality issues., run(), Prompt for Stage 5: Self-Critique Audit.  Contract with app/pipeline/stage5_self

### Community 64 - "Part 4 — Reviewer Transparency and Complete Comparison Workspace"
Cohesion: 0.18
Nodes (11): APIs, Comparison modes, Comparison UI, Dependencies, Done when, Estimated effort, Outcome, Part 4 — Reviewer Transparency and Complete Comparison Workspace (+3 more)

### Community 65 - "ResultWorkspace.jsx"
Cohesion: 0.14
Nodes (11): FeedbackPanel(), TabPanel(), Tabs(), VerificationPanel(), buildDocx(), CRITERION_ORDER, criterionRows(), downloadBlob() (+3 more)

### Community 66 - "stage6_reflection.py"
Cohesion: 0.22
Nodes (11): format_sections_for_prompt(), Any, Format parsed sections into a prompt-ready string, truncating to MAX_SECTION_CHA, _fallback_result(), _parse_final_scores(), Any, Stage 6: Reflection Pass  Input:  llm (LLMService), reviewer_name (str),, Extract criterion scores from <final_scores> block. (+3 more)

### Community 67 - "Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications"
Cohesion: 0.20
Nodes (10): Backend, Dependencies, Done when, Estimated effort, Failure behaviour, Frontend, Outcome, Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications (+2 more)

### Community 68 - "ASSESSMENT_WORKSPACE_REDESIGN_ROADMAP.md"
Cohesion: 0.22
Nodes (8): Backend, Current baseline, Engineering Assessment Workspace — Complete Redesign Roadmap, Frontend, Half-completed frontend features that must not be forgotten, Meaning of “independent” in this roadmap, Non-negotiable execution rules, Product direction

### Community 69 - "AppShell.jsx"
Cohesion: 0.21
Nodes (11): listSessions(), AppShell(), initialCollapsed(), formatWhen(), HistoryTree(), statusBadgeClass(), MobileDrawer(), NAV_ITEMS (+3 more)

### Community 70 - "TopBar.jsx"
Cohesion: 0.22
Nodes (10): App(), TopBar(), ToastContext, ToastProvider(), useTopBar(), preferredTheme(), ThemeContext, ThemeProvider() (+2 more)

### Community 72 - "DocumentPreview.jsx"
Cohesion: 0.39
Nodes (8): getDocumentBlob(), getDocumentHtml(), clearAllHighlights(), DocumentPreview(), drawHighlights(), findItemsForQuote(), findMatchSpan(), scrollIntoContainer()

### Community 73 - "Engineering Report Evaluation — Frontend"
Cohesion: 0.33
Nodes (5): Build for production, Engineering Report Evaluation — Frontend, Environment variables, Getting started, Prerequisites

## Knowledge Gaps
- **187 isolated node(s):** `Config`, `name`, `private`, `version`, `type` (+182 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMService` connect `Async Job Store` to `App Config & Logging`, `stage6_reflection.py`, `Segmentation & Critique Stages`, `Consensus Reconciliation Stage`, `stage7_consensus.py`, `DocumentService`, `stage9_feedback.py`, `LLMService`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `App Config & Logging` to `stage6_reflection.py`, `Part 1 — Complete Frontend Replacement and Core Evaluation Experience`, `Async Job Store`, `session_service.py`, `evaluation.py`, `stage10_verification.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `parse_xml_response()` connect `stage10_verification.py` to `App Config & Logging`, `stage6_reflection.py`, `Segmentation & Critique Stages`, `stage7_consensus.py`, `stage9_feedback.py`, `LLMService`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `Run migrations in 'offline' mode.`, `Run migrations in 'online' mode using an async engine.`, `Config` to the rest of the system?**
  _265 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App Config & Logging` be split into smaller, more focused modules?**
  _Cohesion score 0.1282051282051282 - nodes in this community are weakly interconnected._
- **Should `Verification & Feedback Stages` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Frontend UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.09411764705882353 - nodes in this community are weakly interconnected._