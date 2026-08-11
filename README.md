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
3. Optionally override the model with `OPENROUTER_MODEL=deepseek/deepseek-v4-pro` (default).

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | *(required)* | OpenRouter API key |
| `OPENROUTER_MODEL` | `deepseek/deepseek-v4-pro` | Model to use for all pipeline stages |
| `REVIEWER_TEMPERATURE` | `0.3` | Temperature for reviewer agents |
| `DETERMINISTIC_TEMPERATURE` | `0.0` | Temperature for deterministic stages |
| `SELF_CONSISTENCY_RUNS` | `3` | Odd number of reviewer samples used for consistency checking (minimum `3`) |
| `MAX_DOCUMENT_CHARS` | `200000` | Maximum characters accepted per document |
| `MAX_SECTION_CHARS` | `15000` | Maximum characters per document section |
| `MAX_UPLOAD_BYTES` | `10485760` | Maximum uploaded file size (10 MiB) |
| `MAX_ACTIVE_EVALUATIONS_PER_USER` | `2` | Maximum queued/running jobs per account |
| `APP_HOST` | `0.0.0.0` | Server bind host |
| `APP_PORT` | `8000` | Server bind port |
| `APP_DEBUG` | `false` | Enable debug mode (verbose console logging) |
| `APP_ENVIRONMENT` | `development` | Set to `production` to enforce safe deployment settings |
| `SECRET_KEY` | `change_me` | Long random secret used to sign web sessions and protect `/evaluate/sync` |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed frontend origin and post-login redirect target |
| `AUTH_COOKIE_NAME` | `assessment_session` | Name of the HttpOnly signed-session cookie |
| `AUTH_TOKEN_EXPIRE_MINUTES` | `10080` | Signed-session lifetime (seven days) |
| `AUTH_COOKIE_SECURE` | `false` | Set to `true` when the app is served over HTTPS |
| `ALLOW_PUBLIC_SIGNUP` | `true` | Disable public account creation in production |
| `GOOGLE_CLIENT_ID` | *(empty)* | Google OAuth web-application client ID (enables Google sign-in) |
| `GOOGLE_CLIENT_SECRET` | *(empty)* | Google OAuth web-application client secret |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/google/callback` | Exact authorised Google OAuth callback URI |
| `POSTGRES_USER` | `eval_user` | Postgres user |
| `POSTGRES_PASSWORD` | `eval_password` | Postgres password |
| `POSTGRES_DB` | `eval_platform` | Postgres database name |
| `POSTGRES_HOST` | `localhost` | Postgres host |
| `POSTGRES_PORT` | `5432` | Postgres port |

### Authentication

The application supports both password accounts and Google sign-in. Passwords
are never stored in plain text: the `users` table holds a unique username and
email plus a salted, versioned `scrypt` password hash. Browser sessions use a
signed, `HttpOnly`, `SameSite=Lax` cookie, so the frontend cannot read the
token directly.

To enable Google sign-in, create a **Web application** OAuth client in Google
Cloud, add the exact `GOOGLE_REDIRECT_URI` above to its authorised redirect
URIs, then set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Leave those
values empty if password-only sign-in is desired. In production, use HTTPS,
set `AUTH_COOKIE_SECURE=true`, and change both `FRONTEND_URL` and
`GOOGLE_REDIRECT_URI` to their public HTTPS addresses.

---

## Database

Users, sessions, evaluation versions, and uploaded documents are persisted in
Postgres via SQLAlchemy + Alembic. Every newly created evaluation session is
owned by the signed-in user; session history and uploaded documents are only
available to that owner. The server will not start correctly without a
reachable database.

### Start Postgres (Docker Compose)

```bash
docker compose up -d postgres
```

This starts `postgres:16-alpine` on the private Compose network using credentials
from `.env`. PostgreSQL is not published to a host port. Data persists in the
`postgres_data` volume across restarts.

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

The migration history includes the `users` table and session ownership. Any
sessions created before authentication was introduced have no owner and are not
shown to newly signed-in accounts; assign or migrate those records deliberately
if they need to be retained.

---

## Running the server

```bash
# Development (auto-reload + verbose logging)
APP_DEBUG=true uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

For the containerized application, migration job, durable evaluation worker,
PostgreSQL volume, and Cloudflare Tunnel deployment, follow
[docs/DEPLOYMENT_CLOUDFLARE.md](docs/DEPLOYMENT_CLOUDFLARE.md). Cloudflare is the
public ingress; a persistent Docker host is still required for this Python and
PostgreSQL application.

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

### Authentication and API access

`GET /api/v1/health`, sign-up/sign-in/sign-out, and the Google OAuth start and
callback routes are public. `GET /api/v1/auth/me` and all evaluation, session,
result, and document routes require the signed `HttpOnly` session cookie and
return `401` when the caller is not signed in. In the browser this is sent
automatically. For `curl`, save the cookie during sign-up or login and pass it
to later requests:

```bash
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"ada","email":"ada@example.com","password":"a-long-password"}'

# Use -b cookies.txt with each protected route below.
```

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/signup` | Create a password account and sign in. Body: `username`, `email`, `password` (12+ characters), optional `display_name`. |
| `POST /api/v1/auth/login` | Sign in with an existing password account. Body: `email`, `password`. |
| `POST /api/v1/auth/logout` | Clear the signed-session cookie. |
| `GET /api/v1/auth/me` | Return the signed-in user's public account fields. |
| `GET /api/v1/auth/google/start` | Start Google OAuth sign-in; it redirects to Google, then to the configured frontend. |

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
  -b cookies.txt \
  -F "file=@my_report.pdf"

# Submit raw text
curl -X POST http://localhost:8000/api/v1/evaluate \
  -b cookies.txt \
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
curl -b cookies.txt http://localhost:8000/api/v1/status/YOUR_JOB_ID
```

---

### `GET /api/v1/result/{job_id}`

Retrieve the full evaluation result (only when `status == "complete"`).

Returns `202` while still running, `404` if unknown, `500` if failed.

```bash
curl -b cookies.txt http://localhost:8000/api/v1/result/YOUR_JOB_ID
```

**Response shape:**
```json
{
  "job_id": "...",
  "status": "complete",
  "scoring": {
    "final_score": 68.25,
    "grade_band": "Merit",
    "scoring_complete": true,
    "content_based_estimate": false,
    "assessment_coverage_weight": 1.0,
    "missing_criteria": [],
    "achievement_score": 68.25,
    "final_policy_score": 68.25,
    "achievement_uncertainty_band": [66.45, 70.05],
    "gate_triggered": false,
    "deferred": false,
    "provisional_score": null,
    "provisional_grade_band": null,
    "deferral_reasons": [],
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

**Protected:** requires a signed-in user plus an `x_secret_key` form field
matching `SECRET_KEY` in `.env`, unless `APP_DEBUG=true`.

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/sync \
  -b cookies.txt \
  -F "raw_text=Abstract: ..." \
  -F "x_secret_key=your_secret_key"
```

---

### `GET /api/v1/health`

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","backend":"openrouter","model":"deepseek/deepseek-v4-pro","debug":false}
```

---

### Sessions

A **session** is created per uploaded document; each pipeline run against it (initial evaluation or re-evaluation) is a **version**. History is never destroyed — archiving a session only hides it from the default listing.

#### `GET /api/v1/sessions`

List evaluation sessions (used by the history drawer). Each entry includes its latest version summary.

**Query params:** `include_archived` (bool, default `false`), `limit` (default `50`), `offset` (default `0`)

```bash
curl -b cookies.txt "http://localhost:8000/api/v1/sessions?include_archived=false&limit=50"
```

#### `GET /api/v1/sessions/{session_id}`

Session detail with the full version history.

```bash
curl -b cookies.txt http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID
```

#### `POST /api/v1/sessions/{session_id}/reevaluate`

Re-run the pipeline against the session's stored document, creating a new version and preserving all prior ones.

**Response:**
```json
{"session_id": "uuid", "job_id": "uuid", "version_number": 2, "status": "queued"}
```

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID/reevaluate
```

#### `DELETE /api/v1/sessions/{session_id}`

Archive a session (soft delete — history is preserved and can be restored).

```bash
curl -b cookies.txt -X DELETE http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID
```

#### `POST /api/v1/sessions/{session_id}/unarchive`

Restore an archived session.

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID/unarchive
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
curl -b cookies.txt http://localhost:8000/api/v1/document/YOUR_JOB_ID/meta
```

---

## Scoring and assessment policy

The scoring stage is deterministic Python. Reviewer, audit, reflection, and
consensus stages produce structured assessments carrying a score, confidence,
reasoning, evidence, band-boundary justification, reviewer identity, and
source run. Evidence is whitespace-normalised for automatic verification.
When PDF extraction prevents an otherwise plausible quote from matching
exactly, the pipeline records that as unverified evidence and reduces
confidence rather than automatically discarding the whole assessment. Invalid
score or confidence data is never coerced to a passing level.

### Authoritative rubric and coverage

| Criterion | Weight | Critical | Reviewer coverage |
|---|---:|---|---|
| Technical accuracy | 18% | Yes | Domain Expert |
| Methodology | 15% | Yes | Domain Expert, Methodologist |
| Critical thinking | 14% | No | Methodologist |
| Evidence quality | 12% | No | Domain Expert, Methodologist |
| Structure | 12% | No | Communication Specialist |
| Clarity | 10% | No | Communication Specialist |
| Referencing | 8% | No | Communication Specialist |
| Originality | 7% | No | Communication Specialist |
| Professionalism | 4% | No | Communication Specialist |
| Holistic quality | Validation only | No | Communication Specialist |

The nine weighted criteria total exactly 1.0. `holistic_quality` never enters
the numerical total. The only critical criteria are `technical_accuracy` and
`methodology`; Methodologist does not assess technical accuracy.

### F1–F9

| Formula | Definition |
|---|---|
| F1 | `s_i = level_i / 4` |
| F2 | `A = sum(w_i * s_i)`; if only non-core criteria are unavailable, rescale by the assessed weight coverage. |
| F3 | `achievement_score = 100 * A` |
| F4 | `High = 0.05`, `Medium = 0.20`, `Low = 0.45` |
| F5 | `U = sum(w_i * u_i)`; for a partial estimate, normalise by the assessed weight coverage. |
| F6 | `achievement_uncertainty_band = [max(0, achievement_score - 8U), min(100, achievement_score + 8U)]` |
| F7 | If technical accuracy or methodology is below level 2, `final_policy_score = min(achievement_score, 49)`; otherwise it is `achievement_score`. |
| F8 | Defer only when a core criterion cannot be assessed, less than 50% of weighted coverage is usable, an integrity failure occurs, or consensus explicitly identifies a serious evidence-based issue. Low confidence and high uncertainty are reported, but do not automatically defer a result. |
| F9 | Compare validation-only holistic quality with the grade band from the complete policy score. A disagreement requests moderation only; it never changes the numerical score. |

F6 is a policy uncertainty band, not a statistical confidence interval. It is
always centred on the F3 achievement score, not the gate-adjusted policy score.

Scores are kept to two decimal places for API and presentation. Grade bands use
the unrounded policy score: Distinction `>= 80`, Merit `>= 65 and < 80`, Pass
`>= 50 and < 65`, Fail `< 50`. Therefore display rounding cannot turn `79.5`
into a Distinction. Any integer display is presentation-only.

### Missing data and deferred results

When both core criteria are assessable and at least 50% of the weighted rubric
has usable content evidence, unavailable **non-core** criteria do not erase an
otherwise useful result. The score is normalised over the assessed criteria and
is labelled `content_based_estimate: true`, with
`assessment_coverage_weight` and `missing_criteria` returned so the UI and
exports can make the limitation clear. `scoring_complete` remains `false` to
record the missing rubric data, but the result still has a score and grade
rather than becoming an automatic `DEFERRED` result.

The result is deferred when technical accuracy or methodology cannot be
assessed, weighted coverage is below 50%, an integrity rule fails, or consensus
explicitly flags a serious issue. A serious deferral exposes
`provisional_score` and `provisional_grade_band`; `final_score` remains null.
Missing holistic quality instead returns `holistic_validation.available = false`
and never fabricates a level-2 mark. Frontend and PDF, DOCX, XLSX, and JSON
exports retain these same semantics.

---

## Pipeline Architecture

```
Document Input
  |
  v
Stage 1: Segmentation (LLM, T=0.0)
  |
  v
Stages 2-4: Domain Expert, Methodologist, and Communication Specialist
            (each collects 3 sequential samples)
  |
  v
Stage 5: Self-Critique (one audit per specialist, T=0.0)
  |
  v
Stage 6: Reflection (one reflection per specialist, T=0.0)
  |
  v
Stage 7: Consensus (T=0.0)
  |
  v
Stage 8: Scoring (pure Python, F1-F9)
  |
  v
Stage 9: Feedback Synthesis (T=0.3)
  |
  v
Stage 10: Verification Guard (T=0.0)
  |
  v
EvaluationResult
```
