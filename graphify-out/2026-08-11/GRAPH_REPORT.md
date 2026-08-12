# Graph Report - AI-Evaluation-Work  (2026-08-11)

## Corpus Check
- 120 files · ~42,830 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 783 nodes · 1723 edges · 74 communities (47 shown, 27 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `65db7bc8`
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
- ResultWorkspace.jsx
- stage6_reflection.py
- AppShell.jsx
- TopBar.jsx
- Part 1 — Complete Frontend Replacement and Core Evaluation Experience
- DocumentPreview.jsx

## God Nodes (most connected - your core abstractions)
1. `get_settings()` - 44 edges
2. `User` - 33 edges
3. `parse_xml_response()` - 33 edges
4. `LLMService` - 31 edges
5. `compute_score()` - 22 edges
6. `scan_document()` - 21 edges
7. `apiFetch()` - 18 edges
8. `Session` - 17 edges
9. `run_self_consistent_reviewer()` - 17 edges
10. `parse_review_assessments()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_cookie_authenticated_mutation_requires_trusted_origin()` --calls--> `get_settings()`  [EXTRACTED]
  tests/test_pipeline.py → app/config.py
- `test_evaluate_rejects_submission_at_active_job_limit()` --calls--> `get_settings()`  [EXTRACTED]
  tests/test_pipeline.py → app/config.py
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

## Communities (74 total, 27 thin omitted)

### Community 0 - "App Config & Logging"
Cohesion: 0.19
Nodes (18): compute_median_scores(), Given complete valid reviewer runs, return an aligned structured median., _lower_confidence(), Any, Shared reviewer sampling that preserves validated content judgements., Run reviewer samples without allowing one malformed response to erase all work., run_self_consistent_reviewer(), Any (+10 more)

### Community 1 - "Verification & Feedback Stages"
Cohesion: 0.07
Nodes (24): Settings, _create_user(), main(), _parse_args(), Create a password account without enabling public registration., CriterionAssessment, Any, BaseModel (+16 more)

### Community 2 - "Scoring Engine"
Cohesion: 0.20
Nodes (17): Build an assessment and verify its supporting quotation when possible.      A, validate_assessment(), criteria_for_reviewer(), assessment(), audit_xml(), completed_reviewer(), FakeLLM, Validated assessment, self-consistency, and mocked pipeline-flow tests. (+9 more)

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
Nodes (32): _combine(), Any, Stage 10: Verification Guard  Input:  llm (LLMService),         feedback_out, Deterministically merge the factual verdict with the security scan.     Whichev, Run factual verification and combine it with the security scan., run(), Prompt for Stage 10: Factual Verification.  This stage's LLM prompt covers fac, _char_script() (+24 more)

### Community 7 - "Part 4 — Batch Grading, Analytics, Auth & Hardening"
Cohesion: 0.20
Nodes (10): googleSignInUrl(), RequireAuth(), SubmitForm(), EmptyState(), useAuth(), useTopBarConfig(), Dashboard(), Login() (+2 more)

### Community 8 - "Frontend Build Dependencies"
Cohesion: 0.06
Nodes (30): dependencies, html2pdf.js, pdfjs-dist, react, react-dom, react-is, react-router-dom, recharts (+22 more)

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
Cohesion: 0.06
Nodes (82): get_settings(), User, get_db(), FastAPI dependency — one session per request., Request and response models for application authentication., UserResponse, google_callback(), _google_is_configured() (+74 more)

### Community 24 - "Engineering Report Evaluation API"
Cohesion: 0.24
Nodes (5): _normalise_origin(), OriginProtectionMiddleware, Small ASGI middleware used to harden browser-facing deployments., Require a trusted browser Origin for cookie-authenticated mutations., SecurityHeadersMiddleware

### Community 25 - "DocumentService"
Cohesion: 0.08
Nodes (25): Centralised logging configuration for the API and worker processes., setup_logging(), CriterionScore, EvaluationResult, PipelineStatus, BaseModel, ScoringResult, _elapsed() (+17 more)

### Community 26 - "Engineering Report Evaluation — Frontend"
Cohesion: 0.20
Nodes (9): 1. Prepare production configuration, 2. Build and start the application, 3. Create and connect the Cloudflare Tunnel, 4. Verify before announcing the deployment, 5. Backup and upgrade gate, Deploy with Docker Compose and Cloudflare Tunnel, Go/no-go checklist, Prerequisites (+1 more)

### Community 51 - "rubric_backbone.py"
Cohesion: 0.22
Nodes (9): XML schema fragments used by all specialist reviewer prompts., reviewer_xml_schema(), Shared reviewer prompt material derived from :mod:`app.rubric`., Prompt for the Domain Expert reviewer., Prompt for the Methodologist reviewer., Prompt for the Communication Specialist reviewer., Authoritative rubric policy shared by prompts, pipeline, and scoring.  Keeping t, Render the prompt rubric directly from the authoritative policy. (+1 more)

### Community 55 - "session_service.py"
Cohesion: 0.10
Nodes (51): do_run_migrations(), Run migrations in 'offline' mode., Run migrations in 'online' mode using an async engine., run_migrations_offline(), run_migrations_online(), Base, Document, EvaluationVersion (+43 more)

### Community 56 - "ResultWorkspace.jsx"
Cohesion: 0.20
Nodes (15): extract_scores_from_review(), _fix_ampersands(), parse_review_assessments(), parse_xml_response(), Any, Parse a complete reviewer response while preserving usable evidence.      Stru, Compatibility wrapper returning only a complete, valid assessment map.      Co, LLM output frequently embeds verbatim document text inside attribute     values (+7 more)

### Community 57 - "Engineering Report Evaluation API"
Cohesion: 0.43
Nodes (5): HelpGuide(), sectionForPath(), SECTIONS, TabPanel(), Tabs()

### Community 58 - "stage9_feedback.py"
Cohesion: 0.23
Nodes (14): _extract_block(), _extract_citations(), _extract_point_text(), _extract_points(), Any, Stage 9: Feedback Synthesis  Input:  llm (LLMService),         consensus_out, Best-effort recovery when the LLM's XML is too malformed to parse even     afte, Synthesise written feedback from consensus evaluation and scoring. (+6 more)

### Community 60 - "api.js"
Cohesion: 0.22
Nodes (21): apiFetch(), archiveSession(), evaluateSync(), getCurrentUser(), getDocumentBlob(), getDocumentHtml(), getDocumentMeta(), getResult() (+13 more)

### Community 61 - "RunningEvaluation.jsx"
Cohesion: 0.22
Nodes (11): AppShell(), initialCollapsed(), MobileDrawer(), Sidebar(), TopBar(), TopBarDispatchContext, TopBarProvider(), TopBarValueContext (+3 more)

### Community 62 - "stage10_verification.py"
Cohesion: 0.06
Nodes (40): compute_score(), _grade_band(), _holistic_validation(), _incomplete_result(), Any, Deterministic F1--F9 scoring and explicit deferred-result semantics., Apply the rubric to the content that has actually been assessed.      F1 ``s_i, Entry point for the orchestrator. (+32 more)

### Community 63 - "LLMService"
Cohesion: 0.33
Nodes (7): _failed_audit(), Any, Stage 5: audit the structured median assessment, not a raw last response., Audit the authoritative median assessments and flag invalid audits., run(), _validate_audit(), Prompt for Stage 5: Self-Critique Audit.  Contract with app/pipeline/stage5_se

### Community 65 - "ResultWorkspace.jsx"
Cohesion: 0.15
Nodes (11): FeedbackPanel(), VerificationPanel(), buildDocx(), CRITERION_ORDER, criterionRows(), downloadBlob(), downloadJson(), ResultWorkspace() (+3 more)

### Community 66 - "stage6_reflection.py"
Cohesion: 0.19
Nodes (12): format_sections_for_prompt(), Any, Shared pipeline utilities: section formatting and self-consistency scoring., Format parsed sections into a prompt-ready string, truncating to MAX_SECTION_CHA, Return all parsed submission text for evidence verification.      Unlike promp, sections_as_document_text(), _provisional(), Any (+4 more)

### Community 69 - "AppShell.jsx"
Cohesion: 0.35
Nodes (6): listSessions(), formatWhen(), HistoryTree(), statusBadgeClass(), NAV_ITEMS, useToast()

### Community 70 - "TopBar.jsx"
Cohesion: 0.29
Nodes (7): App(), ToastContext, ToastProvider(), preferredTheme(), ThemeContext, ThemeProvider(), THEMES

### Community 71 - "Part 1 — Complete Frontend Replacement and Core Evaluation Experience"
Cohesion: 0.22
Nodes (9): assessment_to_dict(), AssessmentValidation, evidence_in_document(), normalize_whitespace(), Validated internal assessments used by every scoring stage., Return a JSON-safe copy while supporting existing dict call sites., Validate exact criterion coverage and return serialisable assessments., Verify evidence using whitespace-normalised exact containment only. (+1 more)

### Community 72 - "DocumentPreview.jsx"
Cohesion: 0.57
Nodes (6): clearAllHighlights(), DocumentPreview(), drawHighlights(), findItemsForQuote(), findMatchSpan(), scrollIntoContainer()

## Knowledge Gaps
- **73 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `evaluation.py` to `App Config & Logging`, `Verification & Feedback Stages`, `stage6_reflection.py`, `session_service.py`, `DocumentService`, `stage10_verification.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `docx` connect `DocumentService` to `Frontend Build Dependencies`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `User` (e.g. with `Base` and `AccountCreationDisabledError`) actually correct?**
  _`User` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `ValueError` (e.g. with `.database_url()` and `._max_upload_bytes_must_be_positive()`) actually correct?**
  _`ValueError` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _73 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Verification & Feedback Stages` be split into smaller, more focused modules?**
  _Cohesion score 0.0707070707070707 - nodes in this community are weakly interconnected._
- **Should `Frontend UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.09411764705882353 - nodes in this community are weakly interconnected._