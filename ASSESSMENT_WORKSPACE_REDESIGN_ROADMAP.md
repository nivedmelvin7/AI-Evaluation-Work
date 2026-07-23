# Engineering Assessment Workspace — Complete Redesign Roadmap

**Project:** Engineering Report Evaluation API  
**Inspiration source:** `odysseus.zip`  
**Roadmap purpose:** Convert the current one-page evaluator into a complete engineering assessment workspace through separately executable, vertically complete implementation parts.

---

## Product direction

The current frontend is not being retained as the product design. This roadmap requires a **complete frontend redesign**, not a visual polish pass on the existing page.

The redesigned product will:

- Keep the current React and Vite technology unless a technical blocker is discovered.
- Keep the existing FastAPI evaluation pipeline and scoring engine as the core backend capability.
- Replace the current single-page visual composition, navigation, information hierarchy, and interaction model.
- Use Odysseus as inspiration for its persistent workspace shell, navigation, themes, split panels, history, comparisons, streaming, document workflows, and visual reports.
- Remain an engineering assessment product rather than becoming a general AI chat workspace.
- Support both students improving a report and markers assessing individual reports or cohorts.

The final product should feel like an **Assessment Intelligence Workspace**: focused, transparent, evidence-based, and suitable for serious academic use.

---

## Non-negotiable execution rules

These rules apply whenever a part from this roadmap is implemented.

1. **One part may be requested and implemented at a time.**
2. **Every part is a vertical slice.** Its backend, frontend, data model, validation, errors, tests, and documentation must be completed inside that part.
3. **No part may depend on a later part.** For example, Part 1 must be fully functional without Part 2.
4. A part may depend only on:
   - The current project baseline; or
   - A clearly listed earlier part in the recommended execution order.
5. If an implementation is needed for a feature to work, it belongs in the same part even if it touches several layers.
6. Do not leave placeholder buttons, empty routes, fake charts, mocked production data, or navigation entries for future parts.
7. Features from later parts must not be shown in the UI until those parts are implemented.
8. Each part must pass its own acceptance criteria before the next part begins.
9. Preserve working backend evaluation behaviour while replacing the frontend.
10. Audit existing uncommitted frontend work before editing it. Reuse sound logic where helpful, but do not preserve the current design merely because code already exists.

### Meaning of “independent” in this roadmap

The parts have a recommended order, but each completed part leaves the application usable. There are no forward dependencies. If work stops after any part, all features visible at that point must work completely.

---

## Current baseline

### Backend

- FastAPI application.
- Ten-stage Gemini evaluation pipeline.
- PDF, DOCX, TXT, and raw-text input.
- Asynchronous evaluation with job-status polling.
- Synchronous evaluation protected by a shared secret.
- Deterministic F1–F9 scoring formulas.
- Nine weighted assessment criteria.
- Confidence intervals, uncertainty penalties, deferral, and technical-accuracy gating.
- Structured feedback, consensus, and integrity verification.
- Original-document endpoints for preview.
- In-memory jobs, results, and uploaded-file storage.
- No durable evaluation history or user accounts.

### Frontend

- React 18 and Vite.
- A single `App.jsx` state machine rather than a routed product workspace.
- Report upload or pasted-text submission.
- Polling-based progress tracker.
- Result display with scoring, feedback, verification, metadata, and document preview.

### Half-completed frontend features that must not be forgotten

The working tree contains partially implemented Odysseus-inspired work. These features must be reviewed, corrected, redesigned, tested, and completed inside **Part 1**:

- Dark, Light, Midnight, Paper, Ocean, and Violet themes.
- Theme persistence.
- Toast notifications.
- Score gauge.
- Criteria radar chart.
- Criterion score meters and uncertainty styling.
- PDF report export.
- DOCX report export.
- XLSX score export.
- JSON export.
- Print/export-specific styling.
- Responsive layout changes.
- Document preview and citation-hover behaviour.

They are not considered finished merely because code exists. Part 1 owns their final quality and integration.

---

# Part 1 — Complete Frontend Replacement and Core Evaluation Experience

## Outcome

Replace the current frontend with a cohesive, responsive assessment workspace that supports the complete existing single-report workflow from submission to export.

When Part 1 is complete, the application must work fully with the **current backend**. It must not require persistence, SSE, authentication, batch grading, or any later roadmap part.

## Why this is a complete part

This part includes the entire visible application shell, evaluation submission, polling progress, results, document evidence, export, theming, errors, responsiveness, and accessibility. It does not create navigation to unavailable future features.

## Scope

### 1. New application shell

- Replace the current top-header/single-card layout.
- Add a collapsible desktop sidebar inspired by Odysseus.
- Add a compact icon rail state.
- Add a mobile navigation drawer with backdrop and keyboard dismissal.
- Add a contextual top bar with page title, health state, theme control, and primary action.
- Add a reusable right inspector for document preview and evidence.
- Introduce actual frontend routing for the implemented screens in this part.
- Routes in Part 1:
  - `/` — evaluation dashboard/empty state.
  - `/evaluate/new` — new evaluation.
  - `/evaluate/:jobId/run` — running evaluation.
  - `/evaluate/:jobId/result` — completed result for the current browser session.
- Do not add disabled History, Compare, Cohorts, Analytics, Rubrics, or Users navigation items.

### 2. Design system

- Replace ad hoc and inline styling with documented design tokens.
- Define typography, colour, spacing, radius, border, elevation, motion, and responsive tokens.
- Use interface typography suited to assessment work; reserve monospace for IDs and technical values.
- Provide accessible focus states and keyboard interaction.
- Support reduced motion.
- Provide reusable components:
  - Buttons and icon buttons.
  - Inputs, textareas, selects, and segmented controls.
  - Cards, sections, tabs, badges, status pills, and callouts.
  - Modal, drawer, popover, dropdown, tooltip, toast, skeleton, and empty state.
  - Data table primitives and chart containers.
  - Error boundary and retry state.

### 3. Theme system — complete the half-built work

- Retain only polished themes suitable for this product.
- Required themes: Dark, Light, Midnight, and Paper.
- Ocean and Violet may remain only if they meet the same quality and contrast standards.
- Persist the theme without a flash of the wrong theme on page load.
- Respect the system colour preference on first use.
- Ensure charts, document preview, exports, focus states, and status colours work in every theme.
- Meet WCAG AA contrast for normal interface text.

### 4. Redesigned new-evaluation experience

- Large drag-and-drop upload surface.
- PDF, DOCX, and TXT validation.
- Pasted-text alternative.
- Selected-file summary with name, size, and type.
- Clear validation errors before submission.
- Explain what the evaluation assesses.
- Keep asynchronous evaluation as the normal user path.
- Hide synchronous mode and the shared secret from ordinary users.
- If synchronous mode must remain, place it in a clearly labelled advanced/developer section.
- Prevent duplicate submissions while a request is being created.

### 5. Redesigned running-evaluation experience

- Continue using the current polling endpoints in Part 1.
- Present the ten pipeline stages in an understandable timeline.
- Show current stage, percentage, elapsed time, and plain-language activity.
- Provide reconnect/retry handling when a polling request fails temporarily.
- Distinguish queued, running, failed, and completed states.
- Provide a useful failure screen with retry and start-over actions.
- Avoid implying that individual reviewer events are live until Part 3 implements them.

### 6. Redesigned result workspace

- Product-level result header containing filename, final score, grade, confidence, and status.
- Implement only tabs backed by current result data:
  - Overview.
  - Criteria.
  - Feedback.
  - Evidence/document.
  - Integrity.
  - Technical details.
- Overview:
  - Score gauge.
  - Grade and confidence interval.
  - Criteria summary chart.
  - Strongest and weakest criteria.
  - Highest-priority recommendations.
- Criteria:
  - Sortable, accessible criterion table.
  - Level, weight, score contribution, confidence, rationale, and uncertainty.
  - Text alternative for chart information.
- Feedback:
  - Strengths.
  - Prioritised improvements.
  - Recommended actions.
  - Citation interactions.
- Evidence/document:
  - Original document preview.
  - Page navigation where supported.
  - Citation-to-document highlighting.
  - Clear fallback for unsupported preview formats.
- Integrity:
  - Verification state.
  - Injection result.
  - Release/defer recommendation.
- Technical details:
  - Pipeline metadata.
  - Consensus payload.
  - Job ID.
  - Raw JSON access.

### 7. Complete the charts and status visualisations

- Finish and visually integrate the existing score gauge.
- Finish the criteria radar, or replace it with a clearer bar profile if usability testing shows the radar is harder to read.
- Finish criterion score and uncertainty meters.
- Use consistent grade-band and confidence colours.
- Ensure charts resize correctly and have non-visual equivalents.
- Never use colour as the only indicator.

### 8. Complete notifications and errors

- Finish the toast system.
- Use toasts for transient success and recoverable errors.
- Use inline callouts for errors that block the current workflow.
- Provide accessible live-region announcements.
- Prevent duplicate toast floods during polling.
- Add a top-level frontend error boundary.

### 9. Complete report exports

- Finish PDF, DOCX, XLSX, and JSON exports.
- Give exported files predictable, sanitised filenames.
- PDF must use an assessment-report layout rather than a screenshot-like copy of the app.
- DOCX must contain summary, scoring, criteria, feedback, and integrity sections.
- XLSX must contain at least Summary and Criteria sheets.
- JSON must preserve the complete backend result.
- Export success and failure must be visible.
- Test exports with long feedback and multi-page content.
- Audit the licences of export libraries before release.

### 10. Responsive and accessible completion

- Desktop, tablet, and mobile layouts.
- Right inspector becomes a full-screen sheet or dedicated panel on small screens.
- Tables have a usable small-screen representation.
- Complete keyboard navigation.
- Correct labels, roles, focus management, and announcements.
- Loading skeletons and meaningful empty states.
- Reduced-motion support.
- Test at 200% zoom.

## Backend work

- Only compatibility changes required by the redesigned frontend.
- Do not add persistence or new product domains in this part.
- Normalise error responses if required for reliable UI handling.
- Confirm document preview endpoints return safe content types and useful errors.

## Verification

- Frontend production build succeeds.
- Existing backend tests pass.
- Add frontend tests for critical formatting and state transitions where a test framework is introduced.
- Manual verification of upload, pasted text, progress, failure, result, citations, themes, and every export.
- Mobile and keyboard walkthrough.

## Done when

- The old frontend layout is no longer the product interface.
- A user can submit, monitor, inspect, and export a report without any later part.
- All half-built theme/chart/toast/export/preview features are either completed or deliberately replaced.
- There are no placeholder future screens.
- The new interface is responsive and keyboard usable.

## Dependencies

- Current backend only.
- No dependency on Parts 2–8.

## Estimated effort

**6–9 development days.** This is intentionally larger than a polish phase because it is a complete frontend replacement.

---

# Part 2 — Durable Storage and Complete Evaluation Library

## Outcome

Make evaluations survive restarts and provide a complete history/library workflow for reopening and managing them.

## Why this is a complete part

This part includes storage, migration, APIs, library UI, search, actions, permissions assumptions for the current single-user deployment, and recovery behaviour. It does not require Compare or Analytics.

## Scope

### Backend and data

- Add SQLite persistence through SQLAlchemy 2 or SQLModel.
- Store:
  - Evaluation identity and timestamps.
  - Filename and content type.
  - Status, stage, progress, and error.
  - Final score and grade band.
  - Complete result JSON.
  - Document metadata.
  - Original file or a durable managed file reference.
- Replace in-memory job/result/file storage while preserving existing API behaviour.
- Persist status transitions safely.
- Use atomic writes and clear transaction boundaries.
- Add startup migration/version handling.
- Add retention and deletion rules.

### APIs

- Paginated evaluation list.
- Search and filters.
- Reopen stored result.
- Archive and unarchive.
- Rename and tag.
- Delete with document cleanup.
- Bulk archive/delete where safe.
- Stored document preview after restart.

### Frontend

- Add an Evaluations navigation item only when this part is complete.
- Library table/card view.
- Search by filename, job ID, and tags.
- Filters for date, status, score, grade band, gate, deferral, and integrity.
- Sort by created date, name, score, or uncertainty.
- Reopen a stored result in the Part 1 result workspace.
- Archive, rename, tag, export, and delete.
- Confirmation for destructive actions.
- Pagination or virtualisation for large histories.
- Empty, loading, error, and retry states.

### Reliability

- Completed evaluations survive server restart.
- Running jobs have an explicit restart policy: recover, mark interrupted, or retry safely.
- Database and file records cannot silently diverge.
- Deleting an evaluation cleans up its associated stored file.

## Done when

- History and documents survive restart.
- Library actions work against real persistent data.
- The app remains fully useful if no later part is implemented.
- There are no in-memory-only result paths in production behaviour.

## Dependencies

- Part 1.
- No dependency on Parts 3–8.

## Estimated effort

**4–6 development days.**

---

# Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications

## Outcome

Replace basic polling as the primary experience with a resilient live evaluation stream and complete background-job controls.

## Why this is a complete part

SSE, event production, reconnection, polling fallback, cancellation, retry, navigation safety, and notifications all ship together.

## Scope

### Backend

- Add a per-job event stream using Server-Sent Events.
- Emit typed events:
  - Job queued.
  - Stage started.
  - Stage progress.
  - Stage completed.
  - Reviewer run completed when real data is available.
  - Warning.
  - Failed.
  - Cancelled.
  - Completed.
- Persist important state; do not rely only on in-process event subscribers.
- Add cancel endpoint with safe cooperative cancellation.
- Add retry endpoint with clear rules for new job versus resumed job.
- Keep the existing status endpoint as reconnection and fallback support.
- Ensure slow or disconnected clients cannot block the pipeline.

### Frontend

- EventSource-based live updates.
- Reconnect using the persisted latest state.
- Automatic fallback to polling.
- Live reviewer and stage cards only when backed by emitted events.
- Navigate elsewhere without losing the running job.
- Global background-job indicator.
- Cancel, retry, and reopen actions.
- Optional browser notification when a run completes.
- Do not request notification permission until the user explicitly enables it.

### Failure behaviour

- Network interruption does not create duplicate jobs.
- Refreshing the page reconnects to the correct job.
- Cancellation has an unambiguous final status.
- Retrying links the new attempt to the failed job.

## Done when

- Live progress works end-to-end.
- Polling fallback works when SSE is unavailable.
- Background navigation, refresh, cancellation, retry, and notification behaviour are verified.
- Part 3 does not require Compare or the Improve workflow.

## Dependencies

- Parts 1 and 2.
- No dependency on Parts 4–8.

## Estimated effort

**4–6 development days.**

---

# Part 4 — Reviewer Transparency and Complete Comparison Workspace

## Outcome

Expose how the consensus was produced and provide complete side-by-side comparison for stored evaluations.

## Why this is a complete part

The data contract, storage, comparison engine, reviewer-run views, UI, exports, and edge cases are contained here. It does not require editing or regrading from Part 5.

## Scope

### Reviewer transparency

- Persist individual self-consistency run scores and rationales where available.
- Show each reviewer role and its runs.
- Show median/consensus alongside the individual results.
- Calculate score spread and disagreement per criterion.
- Highlight high disagreement without presenting it as an error.
- Explain uncertainty and how it affects the final score.
- Keep internal chain-of-thought private; expose structured conclusions and evidence only.

### Comparison modes

- Two stored evaluations.
- Two runs of the same document.
- Individual reviewer runs versus consensus.
- Optional blind mode for moderation.

### Comparison UI

- Evaluation selectors with search.
- Side-by-side score and grade cards.
- Criterion delta table.
- Difference chart.
- Feedback added, removed, and changed.
- Confidence, gate, deferral, and integrity comparison.
- Reviewer disagreement heatmap.
- Export comparison as PDF and XLSX.
- Shareable comparison URL using stored evaluation IDs, subject to later authentication rules.

### APIs

- Reviewer-run detail endpoint.
- Normalised compare endpoint.
- Authoritative server-side delta calculations so exports and UI agree.

## Done when

- Users can understand the consensus without inspecting raw JSON.
- Two evaluations can be compared completely.
- Reviewer disagreement is visible and correctly calculated.
- Comparison exports contain the same data as the UI.

## Dependencies

- Parts 1 and 2.
- Part 3 is recommended for richer live reviewer updates but is not required for comparison correctness.
- No dependency on Parts 5–8.

## Estimated effort

**4–6 development days.**

---

# Part 5 — Improve, Version, Re-evaluate, and Measure Progress

## Outcome

Turn one-off evaluation into a complete improvement loop with editable content, version history, re-evaluation, and before/after measurement.

## Why this is a complete part

Document extraction, editable drafts, anchoring, version storage, re-evaluation, autosave, and version comparison are delivered together.

## Scope

### Data model and backend

- Store editable extracted text separately from the immutable original file.
- Add document/evaluation version records.
- Link revised evaluations to their parent evaluation.
- Store draft and submitted versions distinctly.
- Autosave drafts safely.
- Restore a prior draft/version.
- Re-evaluate a selected version through the complete pipeline.
- Preserve the profile and pipeline configuration used by each version.

### Feedback anchoring

- Extend feedback items with section IDs.
- Add character offsets or page-region anchors when reliable.
- Provide section-level fallback when exact anchoring is unavailable.
- Clicking feedback navigates to the relevant document area.
- Mark feedback as addressed, unresolved, or intentionally ignored.

### Improve workspace

- Split editor and feedback layout on desktop.
- Mobile-friendly single-panel mode.
- Original/revised diff.
- Feedback checklist with filters.
- Autosave and save-state indicator.
- Re-evaluate action with cost/time warning where appropriate.
- Result-to-result delta after re-evaluation.
- Resolved, remaining, and newly introduced issues.
- Version timeline and restore.

### Safety

- Original upload is never overwritten.
- Re-evaluation always creates a new evaluation record.
- Autosave conflicts and failed saves are visible.
- DOCX/PDF edits operate on extracted text unless a document-preserving editor is deliberately implemented.

## Done when

- A user can edit, save, restore, re-evaluate, and compare versions.
- Feedback navigation works with documented fallback behaviour.
- Original content and prior evaluations remain recoverable.
- The complete improvement loop works without Batch or Analytics.

## Dependencies

- Parts 1 and 2.
- Part 4 may be reused for comparison UI, but Part 5 must include any version-delta behaviour it needs and must not be left incomplete if Part 4 was skipped.
- No dependency on Parts 6–8.

## Estimated effort

**6–8 development days.**

---

# Part 6 — Versioned Rubrics and Evaluation Profiles

## Outcome

Replace hard-coded assessment configuration with complete, versioned evaluation profiles suitable for EE900, EE990, EE997, EE998, and future assessments.

## Why this is a complete part

Profile storage, validation, APIs, administration UI, evaluation integration, migration, and result traceability ship together.

## Scope

### Profile contents

- Name, module, assessment type, and description.
- Criterion definitions and descriptors.
- Criterion weights.
- Critical criteria and gates.
- Grade bands.
- Deferral rules.
- Required/expected document sections.
- Prompt configuration allowed for administrators.
- Model and self-consistency configuration where safe.
- Export branding and report text.

### Versioning

- Published profiles are immutable.
- Editing a published profile creates a new version.
- Results retain the exact profile version used.
- Draft, published, archived, and default states.
- Duplicate an existing profile.
- Import/export profile JSON.

### Validation

- Weights must be valid and total correctly.
- Grade bands cannot overlap or leave unintended gaps.
- Critical criteria must exist.
- Invalid profiles cannot be published or used.
- Preview deterministic scoring effects before publishing.

### Frontend

- Rubric/profile library.
- Profile editor with guided sections.
- Version history and change summary.
- Read-only published-version view.
- Profile selection during new evaluation.
- Result page displays the exact profile/version used.

## Done when

- Multiple assessment profiles can be created, validated, published, selected, and audited.
- Existing evaluations remain reproducible against their stored profile version.
- The fixed current rubric is migrated into a default versioned profile.

## Dependencies

- Parts 1 and 2.
- No dependency on Parts 7–8.

## Estimated effort

**5–7 development days.**

---

# Part 7 — Cohorts, Batch Grading, Moderation, and Cohort Analytics

## Outcome

Deliver a complete marker workflow: upload a cohort, process it safely, moderate results, analyse the cohort, and export assessment artifacts.

## Why this is a complete part

Batch ingestion without queue controls, moderation, analytics, or exports would be incomplete. Those capabilities are packaged together here as one staff-facing vertical slice.

## Scope

### Cohorts

- Create cohort with module, assessment, academic year, and selected profile.
- Candidate ID and optional anonymised display name.
- Cohort status and audit timestamps.
- Archive and export cohort.

### Batch ingestion

- Multi-file and ZIP upload.
- Preflight validation before processing.
- Duplicate-file and duplicate-candidate handling.
- Bounded concurrency and provider rate-limit protection.
- Per-report queue state and progress.
- Retry only failed/interrupted items.
- Cancel pending items safely.
- Anonymous marking mode.

### Scoreboard and moderation

- Sortable candidate scoreboard.
- Score, grade, confidence, gate, deferral, integrity, and status columns.
- Manual-review queue.
- Marker notes and moderation status.
- Open individual result without losing cohort context.
- Compare selected submissions where Part 4 is present.
- Record manual moderation decisions without silently overwriting AI output.

### Cohort analytics

- Grade distribution.
- Criterion mean, median, and spread.
- Strongest and weakest cohort criteria.
- Confidence and uncertainty distribution.
- Gate, deferral, integrity, and failure rates.
- Reviewer disagreement summary when Part 4 data is present.
- Common improvement categories using deterministic aggregation where possible.
- Clear minimum sample-size handling.

### Exports

- Cohort XLSX scoreboard.
- Cohort analytics PDF.
- ZIP of individual evaluation reports.
- Moderation summary.
- Failed-item report.

## Done when

- A marker can create, process, monitor, moderate, analyse, and export a cohort.
- Rate limits and partial failures do not corrupt the cohort.
- Analytics are calculated from stored authoritative data.
- Individual report workflows remain usable outside cohorts.

## Dependencies

- Parts 1, 2, 3, and 6.
- Part 4 enhances moderation but is not required; Part 7 must hide compare-specific actions if Part 4 is absent.
- No dependency on Part 8.

## Estimated effort

**8–12 development days.**

---

# Part 8 — Accounts, Roles, Security, Backup, Diagnostics, and Production Readiness

## Outcome

Make the application safe and operable as a multi-user deployed assessment system.

## Why this is a complete part

Authentication alone is not production readiness. This part includes ownership migration, authorisation, API tokens, audit, backup, diagnostics, security hardening, and deployment verification.

## Scope

### Accounts and roles

- Secure login and logout.
- Roles:
  - Administrator.
  - Marker.
  - Student/self-evaluator.
- Permission matrix for evaluations, cohorts, rubrics, analytics, exports, and system settings.
- Ownership and visibility rules.
- Migrate existing single-user records to an explicit owner or system account.
- Password change and reset process.
- Optional TOTP 2FA for administrators and markers.

### API tokens

- Create named tokens.
- Show secret only once.
- Store token hashes rather than plaintext.
- Scope and expiry.
- Last-used timestamp.
- Revoke immediately.
- Replace the shared synchronous-evaluation secret with proper authorisation.

### Audit trail

- Login and security events.
- Evaluation creation/deletion.
- Profile publication.
- Cohort changes.
- Moderation decisions.
- Export and token events where appropriate.
- Audit log must be append-oriented and access controlled.

### Prompt and document security

- Explicit prompt-injection pattern checks in addition to model judgement.
- Treat uploaded document content as untrusted context.
- File-type, size, decompression, and content validation.
- Safe document-to-HTML rendering.
- Output sanitisation.
- Rate limits and request-size limits.
- CSRF protection for cookie sessions.
- Secure cookie and production proxy configuration.

### Backup and restore

- Backup database, managed documents, profile versions, and essential settings.
- Exclude secrets unless using an explicitly encrypted secret backup.
- Validate backup before reporting success.
- Restore preview and confirmation.
- Document disaster-recovery procedure.

### Diagnostics and operations

- Health and readiness endpoints.
- Model/provider connectivity.
- Database and storage status.
- Queue and stuck-job visibility.
- Recent error summaries without leaking document content or secrets.
- Application version and migration status.
- Admin diagnostics screen.

### PWA and final client hardening

- Installable application manifest.
- Cache only the safe application shell and immutable static assets.
- Never cache authenticated API responses or report documents in the service worker.
- Offline screen rather than misleading stale assessment data.
- Final accessibility, mobile, performance, and cross-browser audit.

## Done when

- Permissions are enforced on the backend, not only hidden in the UI.
- Existing data has an explicit ownership result after migration.
- Tokens, 2FA option, audit logs, backup/restore, diagnostics, and security controls are verified.
- The application has documented production deployment and recovery procedures.

## Dependencies

- Parts 1 and 2.
- Security and ownership must be applied to every additional implemented earlier part.
- No later roadmap part is required.

## Estimated effort

**8–12 development days.**

---

## Recommended execution order

1. Part 1 — Complete Frontend Replacement and Core Evaluation Experience.
2. Part 2 — Durable Storage and Complete Evaluation Library.
3. Part 3 — Live Pipeline, Background Jobs, Cancel, Retry, and Notifications.
4. Part 4 — Reviewer Transparency and Complete Comparison Workspace.
5. Part 5 — Improve, Version, Re-evaluate, and Measure Progress.
6. Part 6 — Versioned Rubrics and Evaluation Profiles.
7. Part 7 — Cohorts, Batch Grading, Moderation, and Cohort Analytics.
8. Part 8 — Accounts, Roles, Security, Backup, Diagnostics, and Production Readiness.

This sequence prevents forward dependencies. Every part is usable when completed, and later parts extend rather than finish earlier incomplete work.

---

## Odysseus patterns to reuse carefully

| Odysseus source area | Adaptation in this project |
|---|---|
| `static/js/sidebar-layout.js` | Collapsible assessment-workspace sidebar and mobile drawer |
| `static/js/theme.js` | Theme tokens and preference persistence, simplified for academic use |
| `static/js/ui.js` and modal utilities | Toast, clipboard, modal, drawer, and focus patterns |
| `src/visual_report.py` | Editorial evaluation-report structure and print behaviour |
| `static/js/chatStream.js` and `src/event_bus.py` | SSE and background completion patterns |
| `routes/history_routes.py` and session routes | Durable evaluation-list and reopen patterns |
| `static/js/compare/*` and compare routes | Side-by-side comparison and blind moderation concepts |
| Document routes and document UI | Versioning, preview, annotations, and export patterns |
| Auth and API-token routes | Account, role, 2FA, and revocable token patterns |
| `src/prompt_security.py` | Untrusted-context and prompt-injection hardening |
| `static/manifest.json` and `static/sw.js` | Safe installable application shell |

Do not port Odysseus vanilla JavaScript directly into React unless it is a self-contained algorithm or asset with a compatible licence. Recreate the interaction as React components and hooks.

---

## Explicitly excluded product features

The following Odysseus capabilities are not appropriate for an engineering assessment product and are excluded:

- General chat.
- Autonomous agents and MCP tool execution.
- Email and calendar.
- Notes and scheduled personal tasks.
- Model Cookbook and local model serving.
- Image gallery and image editor.
- Speech-to-text and text-to-speech.
- Generic web search and deep-research workflows.
- YouTube processing.

Useful presentation or infrastructure patterns may be borrowed from those areas, but their product functionality must not be added without a separate approved roadmap.

---

## Source archive safety

The uploaded Odysseus archive contains `.env`, database/authentication files, settings, logs, caches, generated content, uploaded content, and model files. These must not be copied into this project.

Only source patterns and appropriately licensed assets may be reused. Before copying any third-party library or bundled asset:

- Confirm its licence.
- Confirm the version is supported and secure.
- Prefer a maintained package dependency where appropriate.
- Record attribution when required.
- Never carry over secrets, user data, or environment-specific configuration.

---

## Definition of complete for every part

A part is complete only when all of the following are true:

- Its user flow works end-to-end with real application data.
- Backend authorisation and validation are enforced where applicable.
- Loading, empty, error, retry, and destructive-action states are handled.
- Desktop and mobile layouts work.
- Keyboard and screen-reader fundamentals are verified.
- Existing relevant tests pass.
- New high-risk logic has automated tests.
- Production frontend build succeeds.
- API and setup documentation are updated.
- No future-part placeholder is visible.
- No known data-loss path remains within the delivered feature.

---

## How to request work on this roadmap

Use one of these forms:

- `Implement Part 1 from ASSESSMENT_WORKSPACE_REDESIGN_ROADMAP.md.`
- `Review Part 3 and give me an implementation plan without coding.`
- `Implement only Part 5 and stop after its acceptance criteria pass.`

When implementing a part, treat the corresponding section as the scope boundary. Do not silently begin the next part.
