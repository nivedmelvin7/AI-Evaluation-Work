# Engineering Report Evaluation API

AI-powered multi-agent pipeline for evaluating engineering reports (EE990/EE997/EE998/EE900 — University of Strathclyde).

---

## Installation

```bash
cd engineering_evaluator
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

### Using Groq (recommended)

1. Get a free API key at [console.groq.com](https://console.groq.com).
2. Set `LLM_BACKEND=groq` and `GROQ_API_KEY=gsk_...` in `.env`.
3. The default models (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) are already configured.

### Using Ollama (local development)

1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull the models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull llama3.2:3b
   ```
3. Set `LLM_BACKEND=ollama` in `.env`.
4. Start Ollama: `ollama serve`.

---

## Running the server

```bash
# Development (auto-reload)
APP_DEBUG=true uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running the test suite

```bash
pytest tests/ -v
```

Tests that call the pipeline stages (test_pipeline.py) do **not** make real LLM calls — they only test the HTTP layer, XML parsing, and scoring formulas.

---

## API Endpoints

### `POST /api/v1/evaluate`

Submit a document for asynchronous evaluation.

**Body** (multipart/form-data):
- `file` — PDF, DOCX, or TXT file **or**
- `raw_text` — plain text string

**Response:**
```json
{"job_id": "uuid", "status": "queued"}
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
    "penalised_score": 67.4,
    "confidence_interval": [63.4, 71.4],
    "gate_triggered": false,
    "deferred": false,
    "criterion_breakdown": { ... }
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
  "consensus": { "scores": { ... } },
  "pipeline_metadata": { ... }
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
# {"status":"ok","backend":"groq","model":"llama-3.3-70b-versatile","debug":false}
```

---

## Scoring Formulas (F1 – F9)

The scoring stage (Stage 8) is pure Python — no LLM call.

| Formula | Name | Expression |
|---------|------|------------|
| F1 | Normalise | `s_i = level_i / 4` |
| F2 | Weighted sum | `A = Σ(w_i × s_i)` |
| F3 | Baseline score | `Score = 100 × A` |
| F4 | Uncertainty mapping | `u_i = {high→0.05, medium→0.20, low→0.45}` |
| F5 | Aggregate uncertainty | `U = Σ(w_i × u_i)` |
| F6 | Penalised score | `Score_pen = Score − 15 × U` |
| F7 | Confidence interval | `[Score_pen − 8U, Score_pen + 8U]` |
| F8 | Non-compensatory gate | If `technical_accuracy < level 2`: cap `Score_pen` at 49 |
| F9 | Deferral rule | If `U > 0.25` OR any critical criterion (technical_accuracy, methodology) has `confidence = low`: mark `DEFERRED` |

**Criterion weights:**

| Criterion | Weight |
|-----------|--------|
| Technical Accuracy | 18% |
| Methodology | 15% |
| Critical Thinking | 14% |
| Evidence Quality | 12% |
| Structure | 10% |
| Clarity | 10% |
| Referencing | 8% |
| Originality | 7% |
| Professionalism | 6% |
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
