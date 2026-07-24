# Engineering Report Evaluation API

AI-powered multi-agent pipeline for evaluating engineering reports (EE990/EE997/EE998/EE900 — University of Strathclyde).

---

## Installation

Requires Python 3.11+ and Docker (for the local Postgres database — see [Database](#database) below).

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### Using OpenRouter

1. Get an API key at [openrouter.ai](https://openrouter.ai/keys).
2. Set `OPENROUTER_API_KEY=your_key_here` in `.env`.
3. Optionally override the model with `OPENROUTER_MODEL=qwen/qwen3.7-plus` (default).

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | *(required)* | OpenRouter API key |
| `OPENROUTER_MODEL` | `qwen/qwen3.7-plus` | Model to use for all pipeline stages |
| `REVIEWER_TEMPERATURE` | `0.3` | Temperature for reviewer agents |
| `DETERMINISTIC_TEMPERATURE` | `0.0` | Temperature for deterministic stages |
| `SELF_CONSISTENCY_RUNS` | `3` | Number of parallel reviewer runs per stage |
| `MAX_DOCUMENT_CHARS` | `200000` | Maximum characters accepted per document |
| `MAX_SECTION_CHARS` | `15000` | Maximum characters per document section |
| `APP_HOST` | `0.0.0.0` | Server bind host |
| `APP_PORT` | `8000` | Server bind port |
| `APP_DEBUG` | `false` | Enable debug mode (verbose console logging) |
| `SECRET_KEY` | `change_me` | Required for the `/evaluate/sync` endpoint |
| `DATABASE_URL` | `postgresql+asyncpg://eval_user:eval_password@localhost:5432/eval_platform` | Postgres connection string (async) |

---

## Database

Sessions, evaluation versions, and uploaded documents are persisted in Postgres via SQLAlchemy + Alembic. The server will not start correctly without a reachable database.

### Start Postgres (Docker Compose)

```bash
docker compose up -d postgres
```

This starts `postgres:16-alpine` on `localhost:5432` with the credentials baked into `docker-compose.yml` (`eval_user` / `eval_password` / `eval_platform`), matching the default `DATABASE_URL` above. Data persists in the `postgres_data` volume across restarts.

```bash
docker compose ps                 # check container health
docker compose logs -f postgres   # tail logs
docker compose down               # stop (keeps the volume/data)
```

### Apply migrations

```bash
alembic upgrade head
```

Run this once after the container is healthy, and again after pulling changes that add new migrations under `alembic/versions/`. To generate a new migration after changing `app/db/models.py`:

```bash
alembic revision --autogenerate -m "describe the change"
```

---

## Running the server

```bash
# Development (auto-reload + verbose logging)
APP_DEBUG=true uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Frontend

A React SPA lives in `frontend/`. In development it proxies `/api` to the backend automatically.

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173
```

For production, build the frontend first and the backend will serve it automatically:

```bash
cd frontend && npm run build
# then start the backend — it detects frontend/dist/ and mounts it at /
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Logging

Structured logs are written to two sinks at startup:

| Sink | Level | Details |
|------|-------|---------|
| Console (stderr) | `INFO` (or `DEBUG` when `APP_DEBUG=true`) | Human-readable |
| `logs/pipeline.log` | `DEBUG` always | Rotating, 10 MB × 5 files |

Each LLM call is logged with model name, temperature, prompt lengths, elapsed time, and response length. Retry attempts are logged at `WARNING` level.

---

## Running the test suite

```bash
pytest tests/ -v
```

Tests that call the pipeline stages (`test_pipeline.py`) do **not** make real LLM calls — they only test the HTTP layer, XML parsing, and scoring formulas.

---

## API Endpoints

### `POST /api/v1/evaluate`

Submit a document for asynchronous evaluation. Creates a new session (and its first version) in the database.

**Body** (multipart/form-data):
- `file` — PDF, DOCX, or TXT file **or**
- `raw_text` — plain text string

**Response:**
```json
{"session_id": "uuid", "job_id": "uuid", "status": "queued"}
```

**Example:**
```bash
# Upload a file
curl -X POST http://localhost:8000/api/v1/evaluate \
  -F "file=@my_report.pdf"

# Submit raw text
curl -X POST http://localhost:8000/api/v1/evaluate \
  -F "raw_text=Abstract: This paper investigates..."
```

---

### `GET /api/v1/status/{job_id}`

Poll the job status.

**Response:**
```json
{
  "job_id": "uuid",
  "session_id": "uuid",
  "version_number": 1,
  "status": "running",
  "stage": "reviewing",
  "progress": 40,
  "error": null
}
```

**Stages in order:** `pending → segmentation → reviewing → auditing → reflecting → consensus → scoring → feedback → verification → complete`

```bash
curl http://localhost:8000/api/v1/status/YOUR_JOB_ID
```

---

### `GET /api/v1/result/{job_id}`

Retrieve the full evaluation result (only when `status == "complete"`).

Returns `202` while still running, `404` if unknown, `500` if failed.

```bash
curl http://localhost:8000/api/v1/result/YOUR_JOB_ID
```

**Response shape:**
```json
{
  "job_id": "...",
  "status": "complete",
  "scoring": {
    "final_score": 68,
    "grade_band": "Merit",
    "achievement_score": 68.0,
    "uncertainty_band": [66.4, 69.6],
    "gate_triggered": false,
    "deferred": false,
    "holistic_validation": {"requires_moderation": false},
    "criterion_breakdown": { "...": "..." }
  },
  "feedback": {
    "overall_assessment": "...",
    "strengths": ["...", "..."],
    "areas_for_improvement": [{"priority": "high", "text": "..."}],
    "recommended_actions": "...",
    "closing": "..."
  },
  "verification": {
    "overall_integrity": "PASS",
    "final_recommendation": "RELEASE",
    "injection_found": false
  },
  "consensus": { "scores": { "...": "..." } },
  "pipeline_metadata": { "...": "..." }
}
```

---

### `POST /api/v1/evaluate/sync`

Synchronous evaluation — waits for completion and returns the result directly.

**Protected:** requires `x_secret_key` form field matching `SECRET_KEY` in `.env`, unless `APP_DEBUG=true`.

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/sync \
  -F "raw_text=Abstract: ..." \
  -F "x_secret_key=your_secret_key"
```

---

### `GET /api/v1/health`

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","backend":"openrouter","model":"qwen/qwen3.7-plus","debug":false}
```

---

### Sessions

A **session** is created per uploaded document; each pipeline run against it (initial evaluation or re-evaluation) is a **version**. History is never destroyed — archiving a session only hides it from the default listing.

#### `GET /api/v1/sessions`

List evaluation sessions (used by the history drawer). Each entry includes its latest version summary.

**Query params:** `include_archived` (bool, default `false`), `limit` (default `50`), `offset` (default `0`)

```bash
curl "http://localhost:8000/api/v1/sessions?include_archived=false&limit=50"
```

#### `GET /api/v1/sessions/{session_id}`

Session detail with the full version history.

```bash
curl http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID
```

#### `POST /api/v1/sessions/{session_id}/reevaluate`

Re-run the pipeline against the session's stored document, creating a new version and preserving all prior ones.

**Response:**
```json
{"session_id": "uuid", "job_id": "uuid", "version_number": 2, "status": "queued"}
```

```bash
curl -X POST http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID/reevaluate
```

#### `DELETE /api/v1/sessions/{session_id}`

Archive a session (soft delete — history is preserved and can be restored).

```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID
```

#### `POST /api/v1/sessions/{session_id}/unarchive`

Restore an archived session.

```bash
curl -X POST http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID/unarchive
```

---

### Document preview

Available only for file uploads (not `raw_text` submissions), keyed by `job_id`.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/document/{job_id}/meta` | File type (`pdf`/`docx`/`txt`), filename, page count |
| `GET /api/v1/document/{job_id}` | Serves the original uploaded file bytes |
| `GET /api/v1/document/{job_id}/html` | HTML rendering for in-browser preview |

```bash
curl http://localhost:8000/api/v1/document/YOUR_JOB_ID/meta
```

---

## Scoring Formulas (F1 – F9)

The scoring stage (Stage 8) is pure Python — no LLM call.

| Formula | Name | Expression |
|---------|------|------------|
| F1 | Normalise | `s_i = level_i / 4` |
| F2 | Weighted sum | `A = Σ(w_i × s_i)` |
| F3 | Achievement score | `Score = 100 × A` |
| F4 | Uncertainty mapping | `u_i = {high→0.05, medium→0.20, low→0.45}` |
| F5 | Aggregate uncertainty | `U = Σ(w_i × u_i)` |
| F6 | Uncertainty band | `[Score − 8U, Score + 8U]`, bounded to the valid score range; this is not a statistical confidence interval |
| F7 | Non-compensatory gate | If technical accuracy or methodology is below level 2: cap the final score at 49 |
| F8 | Deferral rule | If `U > 0.25`, a critical criterion has low confidence, or consensus recommends deferral: mark `DEFERRED` |
| F9 | Holistic validation | A disagreement between the validation-only holistic band and calculated band requires moderation; it does not adjust the score automatically |

Grade bands are calculated from the final bounded score: Distinction `80+`, Merit `65–79`, Pass `50–64`, and Fail below `50`. A deferred result remains unbanded until review.

**Criterion weights:**

| Criterion | Weight |
|-----------|--------|
| Technical Accuracy | 18% |
| Methodology | 15% |
| Critical Thinking | 14% |
| Evidence Quality | 12% |
| Structure | 12% |
| Clarity | 10% |
| Referencing | 8% |
| Originality | 7% |
| Professionalism | 4% |
| Holistic Quality | validation only |

---

## Pipeline Architecture

```
Document Input
     │
     ▼
Stage 1: Segmentation (LLM, T=0.0)
     │  sections[]
     ▼
┌────┴──────────┬────────────────────┐
Stage 2         Stage 3             Stage 4
Domain Expert   Methodologist       Communication
(parallel, 3×)  (parallel, 3×)      Specialist (parallel, 3×)
     │               │                    │
     └───────────────┼────────────────────┘
                     │
                     ▼
         Stage 5: Self-Critique (3× parallel, T=0.0)
                     │
                     ▼
         Stage 6: Reflection (3× parallel, T=0.0)
                     │
                     ▼
         Stage 7: Consensus (T=0.0)
                     │
                     ▼
         Stage 8: Scoring (pure Python, F1–F9)
                     │
                     ▼
         Stage 9: Feedback Synthesis (T=0.3)
                     │
                     ▼
         Stage 10: Verification Guard (T=0.0)
                     │
                     ▼
              EvaluationResult
```
