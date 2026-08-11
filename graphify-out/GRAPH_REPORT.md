# Graph Report - AI-Evaluation-Work  (2026-08-10)

## Corpus Check
- 114 files · ~42,720 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 828 nodes · 1673 edges · 79 communities (51 shown, 28 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 45 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e6ad4b92`
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

## God Nodes (most connected - your core abstractions)
1. `get_settings()` - 34 edges
2. `parse_xml_response()` - 33 edges
3. `User` - 31 edges
4. `LLMService` - 31 edges
5. `compute_score()` - 22 edges
6. `scan_document()` - 21 edges
7. `apiFetch()` - 18 edges
8. `run_self_consistent_reviewer()` - 17 edges
9. `parse_review_assessments()` - 17 edges
10. `format_sections_for_prompt()` - 16 edges

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

## Communities (79 total, 28 thin omitted)

### Community 0 - "App Config & Logging"
Cohesion: 0.17
Nodes (23): get_settings(), compute_median_scores(), format_sections_for_prompt(), Any, Shared pipeline utilities: section formatting and self-consistency scoring., Format parsed sections into a prompt-ready string, truncating to MAX_SECTION_CHA, Given complete valid reviewer runs, return an aligned structured median., _lower_confidence() (+15 more)

### Community 1 - "Verification & Feedback Stages"
Cohesion: 0.11
Nodes (19): 10. Responsive and accessible completion, 1. New application shell, 2. Design system, 3. Theme system — complete the half-built work, 4. Redesigned new-evaluation experience, 5. Redesigned running-evaluation experience, 6. Redesigned result workspace, 7. Complete the charts and status visualisations (+11 more)

### Community 2 - "Scoring Engine"
Cohesion: 0.21
Nodes (15): Build an assessment and verify its supporting quotation when possible.      A, validate_assessment(), assessment(), audit_xml(), completed_reviewer(), FakeLLM, Validated assessment, self-consistency, and mocked pipeline-flow tests., reviewer_xml() (+7 more)

### Community 3 - "Frontend UI Components"
Cohesion: 0.09
Nodes (22): CriteriaRadar(), ORDER, COLUMNS, CONFIDENCE_RANK, CRITERION_ORDER, CriterionTable(), MetadataPanel(), CriterionCallout() (+14 more)

### Community 4 - "System Architecture Overview"
Cohesion: 0.22
Nodes (9): FastAPI, google-genai SDK, httpx (Async HTTP Client), Pydantic v2, PyMuPDF (PDF Parsing), pytest-asyncio (Async Test Support), python-docx (DOCX Parsing), Python Dependencies (requirements.txt) (+1 more)

### Community 6 - "Segmentation & Critique Stages"
Cohesion: 0.11
Nodes (32): _combine(), Any, Stage 10: Verification Guard  Input:  llm (LLMService),         feedback_out, Deterministically merge the factual verdict with the security scan.     Whichev, Run factual verification and combine it with the security scan., run(), Prompt for Stage 10: Factual Verification.  This stage's LLM prompt covers fac, _char_script() (+24 more)

### Community 7 - "Part 4 — Batch Grading, Analytics, Auth & Hardening"
Cohesion: 0.10
Nodes (20): Accounts and roles, API tokens, Audit trail, Backup and restore, Definition of complete for every part, Dependencies, Diagnostics and operations, Done when (+12 more)

### Community 8 - "Frontend Build Dependencies"
Cohesion: 0.06
Nodes (33): Document parsing service. Supports: .pdf (PyMuPDF), .docx (python-docx), .txt (, docx, dependencies, docx, html2pdf.js, pdfjs-dist, react, react-dom (+25 more)

### Community 10 - "Async Job Store"
Cohesion: 0.22
Nodes (14): LLMError, Exception, _make_service(), _mock_response(), Any, Tests for LLMService (OpenRouter is the sole LLM provider).  These mock the HTTP, The app must still boot even with no OpenRouter key configured —     the error s, test_all_retries_exhausted_raises_llm_error() (+6 more)

### Community 11 - "Consensus Reconciliation Stage"
Cohesion: 0.19
Nodes (14): _fallback_section(), _find_snippet(), _normalise_ws(), _parse_markers(), Any, Stage 1: Document Segmentation  Input:  llm (LLMService), document_text (str), Turn boundary markers into full sections by slicing the original text., Return the entire document as one section when segmentation fails. (+6 more)

### Community 12 - "stage7_consensus.py"
Cohesion: 0.24
Nodes (15): _build_consensus_prompt(), _carried_forward(), _coverage_inputs(), _deterministic_provisional_multi(), _lower_confidence(), Any, Stage 7: evidence-based consensus with deterministic coverage safeguards., Keep a usable judgement when a secondary reviewer is unavailable. (+7 more)

### Community 13 - "Request Models"
Cohesion: 0.67
Nodes (3): EvaluationStatusResponse, BaseModel, TextEvaluationRequest

### Community 23 - "evaluation.py"
Cohesion: 0.05
Nodes (61): Settings, get_db(), FastAPI dependency — one session per request., CriterionAssessment, Any, BaseModel, An assessment that is valid only after document evidence is checked., LoginRequest (+53 more)

### Community 24 - "Engineering Report Evaluation API"
Cohesion: 0.17
Nodes (12): Batch ingestion, Cohort analytics, Cohorts, Dependencies, Done when, Estimated effort, Exports, Outcome (+4 more)

### Community 25 - "DocumentService"
Cohesion: 0.13
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
Cohesion: 0.16
Nodes (14): XML schema fragments used by all specialist reviewer prompts., reviewer_xml_schema(), Shared reviewer prompt material derived from :mod:`app.rubric`., Prompt for the Domain Expert reviewer., Prompt for the Methodologist reviewer., Prompt for the Communication Specialist reviewer., criteria_for_reviewer(), Authoritative rubric policy shared by prompts, pipeline, and scoring.  Keeping t (+6 more)

### Community 55 - "session_service.py"
Cohesion: 0.07
Nodes (70): do_run_migrations(), Run migrations in 'offline' mode., Run migrations in 'online' mode using an async engine., run_migrations_offline(), run_migrations_online(), Base, Document, EvaluationVersion (+62 more)

### Community 56 - "ResultWorkspace.jsx"
Cohesion: 0.18
Nodes (17): Validate exact criterion coverage and return serialisable assessments., validate_complete_assessments(), extract_scores_from_review(), _fix_ampersands(), parse_review_assessments(), parse_xml_response(), Any, Parse a complete reviewer response while preserving usable evidence.      Stru (+9 more)

### Community 57 - "Engineering Report Evaluation API"
Cohesion: 0.26
Nodes (9): googleSignInUrl(), health(), RequireAuth(), HealthBadge(), TopBar(), useAuth(), useTopBar(), Login() (+1 more)

### Community 58 - "stage9_feedback.py"
Cohesion: 0.23
Nodes (14): _extract_block(), _extract_citations(), _extract_point_text(), _extract_points(), Any, Stage 9: Feedback Synthesis  Input:  llm (LLMService),         consensus_out, Best-effort recovery when the LLM's XML is too malformed to parse even     afte, Synthesise written feedback from consensus evaluation and scoring. (+6 more)

### Community 60 - "api.js"
Cohesion: 0.25
Nodes (19): apiFetch(), archiveSession(), evaluateSync(), getCurrentUser(), getDocumentBlob(), getDocumentHtml(), getDocumentMeta(), getResult() (+11 more)

### Community 61 - "RunningEvaluation.jsx"
Cohesion: 0.18
Nodes (11): SubmitForm(), useToast(), EmptyState(), FailureScreen(), TopBarDispatchContext, TopBarValueContext, useTopBarConfig(), useTopBarDispatch() (+3 more)

### Community 62 - "stage10_verification.py"
Cohesion: 0.07
Nodes (38): Centralised logging configuration.  Call setup_logging() once at application s, setup_logging(), compute_score(), _grade_band(), _holistic_validation(), _incomplete_result(), Any, Deterministic F1--F9 scoring and explicit deferred-result semantics. (+30 more)

### Community 63 - "LLMService"
Cohesion: 0.33
Nodes (7): _failed_audit(), Any, Stage 5: audit the structured median assessment, not a raw last response., Audit the authoritative median assessments and flag invalid audits., run(), _validate_audit(), Prompt for Stage 5: Self-Critique Audit.  Contract with app/pipeline/stage5_se

### Community 64 - "Part 4 — Reviewer Transparency and Complete Comparison Workspace"
Cohesion: 0.18
Nodes (11): APIs, Comparison modes, Comparison UI, Dependencies, Done when, Estimated effort, Outcome, Part 4 — Reviewer Transparency and Complete Comparison Workspace (+3 more)

### Community 65 - "ResultWorkspace.jsx"
Cohesion: 0.13
Nodes (13): FeedbackPanel(), TabPanel(), Tabs(), VerificationPanel(), buildDocx(), CRITERION_ORDER, criterionRows(), downloadBlob() (+5 more)

### Community 66 - "stage6_reflection.py"
Cohesion: 0.27
Nodes (8): Return all parsed submission text for evidence verification.      Unlike promp, sections_as_document_text(), _provisional(), Any, Stage 6: require complete structured reflection assessments., Reflect only when both the source assessment and audit are complete.      A fa, run(), Prompt for the structured reflection stage.

### Community 67 - "Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications"
Cohesion: 0.20
Nodes (10): Backend, Dependencies, Done when, Estimated effort, Failure behaviour, Frontend, Outcome, Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications (+2 more)

### Community 68 - "ASSESSMENT_WORKSPACE_REDESIGN_ROADMAP.md"
Cohesion: 0.22
Nodes (8): Backend, Current baseline, Engineering Assessment Workspace — Complete Redesign Roadmap, Frontend, Half-completed frontend features that must not be forgotten, Meaning of “independent” in this roadmap, Non-negotiable execution rules, Product direction

### Community 69 - "AppShell.jsx"
Cohesion: 0.23
Nodes (10): listSessions(), AppShell(), initialCollapsed(), formatWhen(), HistoryTree(), statusBadgeClass(), MobileDrawer(), NAV_ITEMS (+2 more)

### Community 70 - "TopBar.jsx"
Cohesion: 0.29
Nodes (7): App(), ToastContext, ToastProvider(), preferredTheme(), ThemeContext, ThemeProvider(), THEMES

### Community 71 - "Part 1 — Complete Frontend Replacement and Core Evaluation Experience"
Cohesion: 0.25
Nodes (7): assessment_to_dict(), AssessmentValidation, evidence_in_document(), normalize_whitespace(), Validated internal assessments used by every scoring stage., Return a JSON-safe copy while supporting existing dict call sites., Verify evidence using whitespace-normalised exact containment only.

### Community 72 - "DocumentPreview.jsx"
Cohesion: 0.57
Nodes (6): clearAllHighlights(), DocumentPreview(), drawHighlights(), findItemsForQuote(), findMatchSpan(), scrollIntoContainer()

### Community 73 - "Engineering Report Evaluation — Frontend"
Cohesion: 0.83
Nodes (3): getStepState(), ProgressTracker(), STAGES

## Knowledge Gaps
- **159 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `App Config & Logging` to `evaluation.py`, `stage10_verification.py`, `session_service.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `User` (e.g. with `Base` and `DuplicateAccountError`) actually correct?**
  _`User` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _159 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Verification & Feedback Stages` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Frontend UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.09411764705882353 - nodes in this community are weakly interconnected._
- **Should `Segmentation & Critique Stages` be split into smaller, more focused modules?**
  _Cohesion score 0.10810810810810811 - nodes in this community are weakly interconnected._
- **Should `Part 4 — Batch Grading, Analytics, Auth & Hardening` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._