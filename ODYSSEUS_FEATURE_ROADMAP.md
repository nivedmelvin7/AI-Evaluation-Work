# Odysseus-Inspired Feature Roadmap

**For:** Engineering Report Evaluation API (EE990/EE997/EE998/EE900 — University of Strathclyde)
**Source of ideas:** `odysseus` (self-hosted AI workspace) — features filtered down to the subset that genuinely elevates a *report-evaluation* tool.
**Goal:** Turn a solid evaluation API into a product markers and students love.

---

## How to use this document

This roadmap is split into **4 self-contained parts**. Each part is a task package that can be picked up at a **different time**, by a different session, with everything needed inside it:

- **Goal** — one-line outcome
- **Why it stands out** — the value
- **Depends on** — what must exist first (parts are ordered so this is minimal)
- **Mine from odysseus** — exact source files to copy patterns/assets from
- **Backend work** / **Frontend work** — concrete steps + files to create/modify *in this repo*
- **New dependencies**
- **Done when** — acceptance criteria
- **Effort** — rough dev-days

> **Recommended order:** 1 → 2 → 3 → 4. Parts 3 and 4 lean on Part 2's persistence, but each part still delivers standalone value and can be reordered if you accept the noted trade-offs.

### Assumptions (override any of these and I'll adjust the plan)

1. **Keep React.** We port odysseus's *look and feel* (themes, charts, report styling, toasts) into the existing React SPA rather than replacing it with odysseus's vanilla-JS shell. Lowest risk, keeps your architecture.
2. **Dual audience.** Students (self-checking → improve loop, polished PDF) *and* markers (batch, analytics, export) are both served, spread across the phases.
3. **SQLite for persistence** (Part 2). ChromaDB/RAG (Part 4) is optional/stretch and the only piece that adds a heavy external service.
4. **Single deployable unit stays the default** — backend serves the built frontend; no mandatory new services except where called out.

---

## Where this project stands today (baseline)

**Backend** — FastAPI, 10-stage LLM pipeline (Gemini), pure-Python scoring (F1–F9).
- Async job model: `POST /api/v1/evaluate` → poll `GET /status/{id}` → `GET /result/{id}`; plus `POST /evaluate/sync` gated by a single `SECRET_KEY`.
- **Persistence: none.** `app/utils/file_store.py` is an in-memory `dict`; the job/result registry is in-memory too. **Everything is lost on restart.**
- Deps: `fastapi`, `google-genai`, `pymupdf`, `python-docx`. No DB, no auth framework, no vector store.

**Frontend** — React 18 + Vite + `pdfjs-dist`. 10 components.
- Flow: `App.jsx` (state machine: idle→polling→done) → `SubmitForm` → `ProgressTracker` (2s polling) → `ResultView` (`ScoreCard`, `CriterionTable`, `FeedbackPanel`, `VerificationPanel`, `MetadataPanel`, `DocumentPreview` with citation highlighting).
- Export today = **raw JSON download only**. No themes, no charts, no toasts, no PDF/DOCX/XLSX libs.
- CSS already uses design tokens (`--text-muted`, `--border`, etc.) → theming drops in cleanly.

---

## Feature map at a glance

| # | Part | Headline features | Primary surface | Effort |
|---|------|-------------------|-----------------|--------|
| 1 | **UI Polish & Report Export** | Theme system, score gauge + criteria radar, toasts, polished HTML/PDF report, DOCX/XLSX export | Frontend | ~3–4 d |
| 2 | **Persistence, History & Compare** | SQLite store, evaluation history, blind side-by-side compare (2 reports / 3 self-consistency runs), before/after diff | Backend + Frontend | ~4–5 d |
| 3 | **Improve Loop & Live Streaming** | Inline editor with anchored feedback, edit→re-grade→score diff, SSE streaming progress, keyboard shortcuts, onboarding, PWA | Full-stack | ~5–6 d |
| 4 | **Batch Grading, Analytics, Auth & Hardening** | Batch/cohort grading, analytics dashboard, real auth + API tokens + 2FA, injection hardening, RAG rubric grounding | Backend-heavy | ~6–8 d |

---

# Part 1 — UI Polish & Report Export

**Goal:** Make the app look premium and let users walk away with a polished, shareable evaluation report (PDF/DOCX/XLSX), not raw JSON.

**Why it stands out:** First impression + the artifact people keep. Highest visual payoff for the least architectural risk. Directly satisfies the "I want frontend changes from odysseus" request.

**Depends on:** Nothing. Pure frontend + optional server-side HTML template. Safe to do first.

**Mine from odysseus:**
- `static/js/theme.js` — ~20 theme presets + custom color editor + `prefers-color-scheme`.
- `src/visual_report.py` — turns report data into a self-contained editorial HTML page (hero, auto TOC, print/share toolbar, dark/light). This is the exact pattern for an "Evaluation Report" export.
- `static/js/ui.js` (`showToast`, `showError`, `copyToClipboard`) and `static/js/spinner.js`.
- `static/lib/html2pdf.bundle.min.js`, `xlsx.full.min.js`, `docx.umd.min.js`, `mammoth.browser.min.js`, `highlight.min.js` — self-contained, drop straight in.

### Frontend work (this repo)
1. **Theme system**
   - Add `frontend/src/theme/ThemeContext.jsx` — React context + `localStorage` persistence + `prefers-color-scheme` default.
   - Port a small subset of odysseus `THEMES` (e.g. `dark`, `light`, `midnight`, `paper`, plus 2–3 accents) into CSS-variable sets in `frontend/src/index.css` (`:root[data-theme="…"]`).
   - Add a theme toggle/selector to `App.jsx` header (next to `HealthBadge`).
2. **Richer result visuals** (`ResultView` / new components)
   - `ScoreGauge.jsx` — radial gauge for `scoring.final_score` with grade-band color + confidence-interval band (`scoring.confidence_interval`).
   - `CriteriaRadar.jsx` — radar chart of the 9 criteria from `scoring.criterion_breakdown` (weight-aware).
   - Upgrade `CriterionTable` rows with inline bar meters + uncertainty coloring.
3. **Toasts & spinners** — add `frontend/src/components/Toast.jsx` + a `useToast()` hook; replace the inline `ErrorBanner` path in `App.jsx` and success messages (e.g. "Report exported").
4. **Export menu** in `ResultView` header (replace the lone "Download JSON"):
   - **PDF** — render the report section to PDF via `html2pdf` (client-side; keep JSON as a secondary option).
   - **XLSX** — criterion breakdown → spreadsheet via `xlsx`.
   - **DOCX** — feedback + scores → Word via `docx`.
5. *(Optional, higher-fidelity)* Server-side report: add `GET /api/v1/report/{job_id}.html` that renders a `visual_report.py`-style standalone HTML (Jinja template in `app/`), then let the client "Print → Save as PDF". Gives editorial-grade output independent of screen layout.

### New dependencies
- Frontend: `recharts` (gauge/radar/bars), `html2pdf.js`, `xlsx`, `docx`. (Or copy the vendored `static/lib/*.min.js` for offline/self-hosted parity.)
- Backend (only if doing the optional server-side report): `jinja2`, `markdown`, `beautifulsoup4`.

### Done when
- [ ] User can switch dark/light (+ at least 2 accent themes); choice persists across reloads.
- [ ] Result view shows a score gauge and a criteria radar driven by real result data.
- [ ] One-click export produces a clean **PDF**; XLSX and DOCX exports work.
- [ ] Errors and successes surface as toasts, not just inline banners.

**Effort:** ~3–4 dev-days.

---

# Part 2 — Persistence, History & Compare

**Goal:** Stop losing evaluations on restart. Store them, let users browse past runs, and compare two reports — or the 3 self-consistency reviewer runs — side by side.

**Why it stands out:** Converts a one-shot tool into a system of record. "Before vs after" and "which reviewer disagreed" are exactly what graders want to see.

**Depends on:** Nothing hard. Compare's "before/after" is richer once history exists (this part provides it). The 3-run compare only needs per-run scores surfaced from the pipeline.

**Mine from odysseus:**
- `core/database.py` (SQLAlchemy models + `SessionLocal`) and `src/database.py` — schema/session patterns.
- `routes/history_routes.py`, `routes/session_routes.py` — list/re-open endpoints.
- `routes/compare_routes.py` + `static/js/compare/{scoreboard,vote,panes,state,selector}.js` — blind A/B UI, scoreboard, and vote/tally patterns.

### Backend work (this repo)
1. **Introduce SQLite** (SQLAlchemy or SQLModel):
   - `app/db.py` — engine + session (`sqlite:///./data/app.db`).
   - Models in `app/models/db_models.py`:
     - `Evaluation(job_id PK, created_at, filename, status, stage, final_score, grade_band, result_json, doc_meta_json)`
     - `StoredFile(job_id FK, content BLOB, content_type, filename, pages_json)` — replaces the in-memory `file_store`.
2. **Migrate the in-memory registries**:
   - Rewrite `app/utils/file_store.py` to read/write `StoredFile` (keep the same method signatures so callers don't change).
   - Persist job status + final result where the pipeline currently holds them in memory (in `app/routers/evaluation.py` / orchestrator). Write status transitions through each pipeline stage.
3. **New endpoints**:
   - `GET /api/v1/history?limit=&offset=` → list past evaluations (id, filename, date, score, band).
   - `GET /api/v1/result/{job_id}` already exists → now served from DB (survives restart).
   - `DELETE /api/v1/evaluation/{job_id}`.
   - `GET /api/v1/consistency/{job_id}` → per-run scores for the 3 self-consistency reviewer runs (surface data the pipeline already computes; expose it in `pipeline_metadata`/`consensus`).
   - `POST /api/v1/compare` `{job_id_a, job_id_b}` → aligned criterion-by-criterion diff.

### Frontend work (this repo)
1. **History view** — new route/panel `History.jsx`: table of past evaluations, click to re-open a stored `ResultView`. Add a nav entry in the header.
2. **Compare view** — `CompareView.jsx`:
   - **Two-report mode:** pick two evaluations → side-by-side score gauges + per-criterion diff (▲/▼ deltas), reusing Part 1 charts.
   - **Self-consistency mode:** show the 3 reviewer runs per criterion (mini-scoreboard) to expose disagreement/variance — the honest story behind the consensus score.
   - Optional **blind toggle** (hide which is which) borrowed from odysseus compare.

### New dependencies
- Backend: `sqlalchemy>=2.0` (or `sqlmodel`). SQLite ships with Python.

### Done when
- [ ] Evaluations and uploaded files survive a server restart (stored in `data/app.db`).
- [ ] A history list shows past runs and can re-open any result.
- [ ] Two evaluations render side-by-side with per-criterion deltas.
- [ ] The 3 self-consistency runs are viewable per criterion (variance visible).

**Effort:** ~4–5 dev-days.

---

# Part 3 — Improve Loop & Live Streaming

**Goal:** Let a user edit their report against anchored feedback, re-evaluate, and see the score move — and make the pipeline feel *alive* with live streaming instead of 2-second polling.

**Why it stands out:** This is the killer *educational* feature — a one-shot grade becomes a learning loop ("fix methodology → +6"). Streaming makes the 30–120s wait engaging (watch each agent land its verdict).

**Depends on:** Part 2 (persistence) so edits/re-grades and their score history are stored and diffable. Streaming itself is independent.

**Mine from odysseus:**
- `static/js/document.js` + `static/js/editor/` — multi-tab markdown editor with AI edits/suggestions and anchored annotations.
- `static/js/chatStream.js` + `src/event_bus.py` — SSE streaming pattern and event bus for emitting per-stage progress.
- `static/js/keyboard-shortcuts.js`, `static/js/tourHints.js` / `tourAutoplay.js` — shortcuts + onboarding.
- `static/manifest.json`, `static/sw.js` — PWA install + offline shell.

### Backend work (this repo)
1. **Streaming progress**: add `GET /api/v1/stream/{job_id}` (SSE via FastAPI `StreamingResponse`). Emit events from the orchestrator through a lightweight event bus (`app/utils/event_bus.py`, modeled on odysseus `src/event_bus.py`): `stage_started`, `agent_result`, `stage_complete`, `done`. Keep polling as a fallback.
2. **Re-evaluate endpoint**: `POST /api/v1/reevaluate` `{parent_job_id, edited_text}` → runs the pipeline on edited text, stores the new evaluation linked to the parent (`parent_job_id` column from Part 2) for diffing.
3. *(Optional)* Anchor feedback to source: extend feedback items with character offsets / section ids so the editor can highlight the exact spans referenced.

### Frontend work (this repo)
1. **Editor + improve loop** — `ImproveView.jsx`: two-pane layout — editable report text on the left (seed from the uploaded doc's extracted text), feedback list on the right with items anchored to the referenced spans. "Re-evaluate" button → shows **score diff vs previous** (reuse Part 1 gauges + Part 2 diff).
2. **Live progress** — replace the polling loop in `App.jsx` with an `EventSource` subscription; stream stage transitions and per-agent verdicts into `ProgressTracker` (show reviewer agents completing in real time).
3. **Keyboard shortcuts** — `useKeyboardShortcuts()` hook: `?` overlay, `n` new evaluation, `e` export, `Esc` closes panels/modals.
4. **Onboarding & empty states** — first-run tour hints; friendlier empty/error states (a ROADMAP item odysseus itself flags).
5. **PWA** — add `manifest.json` + service worker so the app is installable and responsive on mobile.

### New dependencies
- Frontend: a lightweight editor (`@uiw/react-md-editor` or CodeMirror). No new backend deps (SSE is stdlib-friendly in FastAPI/Starlette).

### Done when
- [ ] User can edit report text and re-evaluate; the UI shows the score delta vs the prior run.
- [ ] Progress streams live (per-stage / per-agent) instead of 2s polling.
- [ ] `?` shows a shortcuts overlay; core actions have keys; `Esc` closes panels.
- [ ] App is installable (PWA) and usable on a phone.

**Effort:** ~5–6 dev-days.

---

# Part 4 — Batch Grading, Analytics, Auth & Hardening

**Goal:** Serve the marker workflow (grade a whole cohort, see aggregate analytics) and make it safe to deploy for multiple users.

**Why it stands out:** This is the real staff use case — upload 30 submissions, get a scoreboard, spot that "Referencing" is the cohort's weakest criterion — behind proper accounts and API tokens.

**Depends on:** Part 2 (persistence) for storing cohorts, results, and users.

**Mine from odysseus:**
- `src/analytics.py` — aggregate stats patterns.
- `routes/auth_routes.py`, `routes/api_token_routes.py`, `core/auth.py`, `src/api_key_manager.py`, `src/secret_storage.py` — auth, per-user API tokens, 2FA.
- `src/prompt_security.py` — prompt-injection detection (strengthens your Stage 10 verification guard).
- `src/rag_manager.py`, `src/rag_vector.py`, `src/chroma_client.py`, `src/embeddings.py` — RAG grounding (stretch).

### Backend work (this repo)
1. **Batch grading**:
   - `POST /api/v1/batch` — accept multiple files (or a zip) → create a `Cohort` + child `Evaluation` rows; process with bounded concurrency (respect `SELF_CONSISTENCY_RUNS` and rate limits).
   - `GET /api/v1/batch/{cohort_id}` — scoreboard: per-report score/band + status.
2. **Analytics**:
   - `GET /api/v1/analytics?cohort_id=` → grade distribution, per-criterion averages, most common improvement areas, deferral/gate rates. Pure Python over stored results (no LLM cost), mirroring `analytics.py`.
3. **Auth & tokens** (replace the single `SECRET_KEY`):
   - `User` table + login (session or JWT), `core/auth.py`-style middleware.
   - Per-user **API tokens** for programmatic `/evaluate` (create/revoke), modeled on `api_token_routes.py`.
   - Optional **2FA** (TOTP) for admin accounts.
   - Gate `/evaluate/sync`, batch, and analytics behind auth instead of the shared secret.
4. **Prompt-injection hardening**: fold `prompt_security.py` checks into Stage 10 (`app/pipeline/stage10_verification.py`) so `injection_found` is backed by explicit detectors, not just model judgment.
5. *(Stretch)* **RAG rubric grounding**: index the actual EE990/997/998/900 marking scheme in ChromaDB; retrieve relevant rubric text per criterion so feedback cites the rubric. Adds ChromaDB + an embeddings endpoint (the one heavy new service).

### Frontend work (this repo)
1. **Batch upload + cohort scoreboard** — `BatchView.jsx`: multi-file drop, live per-report progress, sortable scoreboard (name, score, band, flags).
2. **Analytics dashboard** — `AnalyticsView.jsx`: grade-distribution histogram, per-criterion average bars, "weakest criterion" callout, deferral/gate counts (reuse Part 1 charts).
3. **Auth UI** — login page, API-token management screen, per-user settings.

### New dependencies
- Backend: `passlib[bcrypt]` + `python-jose` (or `pyjwt`) for auth; `pyotp` for 2FA; `chromadb` + an embeddings client *only if* doing the RAG stretch.

### Done when
- [ ] Upload many reports at once and see a cohort scoreboard.
- [ ] Analytics dashboard shows grade distribution + per-criterion averages from stored results.
- [ ] Login works; the shared `SECRET_KEY` is replaced by per-user auth + revocable API tokens.
- [ ] Stage 10 flags known prompt-injection patterns via explicit detectors.
- [ ] *(Stretch)* Feedback cites rubric text retrieved via RAG.

**Effort:** ~6–8 dev-days (≈4–5 without the RAG stretch).

---

## Appendix A — Reusable asset inventory (copy-paste, minimal rewrite)

| Asset | odysseus path | Use in this project |
|-------|---------------|---------------------|
| PDF export | `static/lib/html2pdf.bundle.min.js` | Part 1 — report → PDF |
| Spreadsheet export | `static/lib/xlsx.full.min.js` | Part 1 — criterion breakdown → XLSX |
| Word export/import | `static/lib/docx.umd.min.js`, `mammoth.browser.min.js` | Part 1 — feedback → DOCX; ingest .docx |
| Syntax highlight | `static/lib/highlight.min.js` | Part 1/3 — code/section highlighting |
| Theme presets + color editor | `static/js/theme.js` | Part 1 — theme system |
| Toasts / clipboard / spinner | `static/js/ui.js`, `spinner.js` | Part 1 — UX primitives |
| Editorial HTML report generator | `src/visual_report.py` | Part 1 — server-side report |
| SSE streaming + event bus | `static/js/chatStream.js`, `src/event_bus.py` | Part 3 — live progress |
| Editor + annotations | `static/js/document.js`, `static/js/editor/` | Part 3 — improve loop |
| Blind compare + scoreboard | `routes/compare_routes.py`, `static/js/compare/*` | Part 2 — compare view |
| History/session endpoints | `routes/history_routes.py`, `session_routes.py` | Part 2 — history |
| DB models/session | `core/database.py` | Part 2 — SQLite |
| Analytics | `src/analytics.py` | Part 4 — dashboard |
| Auth / tokens / 2FA | `routes/auth_routes.py`, `api_token_routes.py`, `core/auth.py` | Part 4 — auth |
| Prompt-injection detectors | `src/prompt_security.py` | Part 4 — Stage 10 hardening |
| RAG / vectors | `src/rag_manager.py`, `chroma_client.py`, `embeddings.py` | Part 4 — rubric grounding |
| PWA shell | `static/manifest.json`, `sw.js` | Part 3 — installable app |

## Appendix B — Explicitly out of scope (odysseus features that don't fit a report grader)

Chat, agents/MCP tool-running, model Cookbook (hardware fit / model serving), email (IMAP/SMTP), calendar (CalDAV), notes/tasks, image gallery/editor, TTS/STT, YouTube, deep-research web crawling. These are workspace features irrelevant to evaluating engineering reports and are intentionally excluded — though *visual-report rendering* (from deep research) and *compare* (from the model arena) are borrowed above.

## Appendix C — Decisions to confirm before executing a part

- **Part 1:** vendored `static/lib/*.min.js` (offline/self-hosted) vs npm packages (`recharts`, `html2pdf.js`, `xlsx`, `docx`)?
- **Part 2:** SQLAlchemy vs SQLModel? Keep raw JSON blob for results, or fully normalize criteria into tables?
- **Part 3:** Editor library (`@uiw/react-md-editor` vs CodeMirror)? Anchor feedback by char-offset or by section id?
- **Part 4:** Session-cookie vs JWT auth? Include the RAG stretch (adds ChromaDB) or defer it?
