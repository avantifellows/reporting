---
name: architecture
description: How the major pieces of this project connect and flow. Load when working on system design, integrations, or understanding how components interact.
triggers:
  - "architecture"
  - "system design"
  - "how does X connect to Y"
  - "integration"
  - "flow"
edges:
  - target: context/stack.md
    condition: when specific technology details are needed
  - target: context/decisions.md
    condition: when understanding why the architecture is structured this way
  - target: context/reports.md
    condition: when working on report data schemas or the v1/v2/v3 lookup chain
  - target: context/auth.md
    condition: when working on launch tokens or report access control
last_updated: 2026-07-09
---

# Architecture

## System Overview

Request comes in via AWS API Gateway → Lambda runs the FastAPI app through the
Mangum adapter (`app/main.py`, `handler = Mangum(app)`) → matched to one of three
router classes (`StudentQuizReportsRouter`, `SessionQuizReportsRouter`,
`FormResponsesRouter`), all mounted under the `/reports` prefix → the endpoint
closure calls a DB wrapper class (`ReportsDB`, `QuizDB`, `BigQueryDB`,
`SessionsDB`, `FormResponsesDB`) → the wrapper queries its data source
(DynamoDB, MongoDB Atlas, BigQuery, Firestore) → the endpoint assembles a
`report_data` dict and renders a Jinja2 template from `app/templates/` →
if `?format=pdf`, the rendered HTML is passed to `convert_template_to_pdf`
(inlines CSS + images, POSTs to an external HTML-to-PDF service) → response
returned as HTML, PDF stream, or JSON.

All DB clients are initialized once at module import in `app/main.py` via
`app/internal/db.py`, then injected into router classes as constructor args.

## Key Components

- **Router classes** (`app/routers/`) — one class per report family; each exposes a `router` `@property` that builds an `APIRouter` with endpoints defined as closures. Depends on DB wrappers injected in `main.py`.
- **DB wrappers** (`app/db/`) — one class per data source; the only place queries live. `ReportsDB`/`FormResponsesDB` (DynamoDB), `QuizDB` (MongoDB aggregation for live stats), `BigQueryDB` (qualification data), `SessionsDB` (Firestore Sessions collection).
- **`app/internal/db.py`** — creates DynamoDB/Mongo/BigQuery clients; falls back to `load_dotenv("../.env.local")` when env vars are absent (local dev). BigQuery credentials come from AWS Secrets Manager.
- **`app/auth/` + `app/utils/report_launch.py`** — launch-token verification against the portal backend and the redirect-with-cookie handoff. See `context/auth.md`.
- **`app/utils/pdf_converter.py`** — converts a `TemplateResponse` to PDF: inlines `app/static/style.css` (or a hard-coded default), base64-inlines local images, POSTs to `HTML_TO_PDF_SERVER_URL`.
- **`app/utils/llm_summary.py`** — `LLMSummaryGenerator` produces theme summaries for form responses via OpenRouter (model "google/gemini-3-flash-preview", async OpenAI SDK).

## External Dependencies

- **DynamoDB** — report storage: `student_quiz_reports` (v1) and `student_quiz_reports_v2` tables. Table names are hard-coded in `app/db/reports_db.py`, not read from env.
- **MongoDB Atlas** — `quiz.quizzes` collection + per-quiz session documents; used for live quiz stats via aggregation pipeline (`QuizDB.get_live_quiz_stats`).
- **BigQuery** — `avantifellows.prod_af_db.student_profile_al` for qualification status / revision recommendations (v3 reports). Falls back to safe defaults on any error.
- **Firestore** — `Sessions` collection (temporary home until a Postgres migration); maps session_id → quiz_id + dates for live session reports.
- **Portal backend** (`PORTAL_BACKEND_URL`) — verifies launch tokens at `/auth/verify`; this service never validates tokens itself.
- **HTML-to-PDF service** (`HTML_TO_PDF_SERVER_URL`) — external Lambda/service that renders the inlined HTML; this repo never runs a headless browser.
- **OpenRouter** (`OPENROUTER_API_KEY`) — LLM summaries for form responses.

## What Does NOT Exist Here

- **No report generation/writing** — this service is read-only over DynamoDB; the ETL that writes reports lives in other Avanti Fellows systems.
- **No frontend app** — Gurukul (separate repo) and quiz.avantifellows.org link into these server-rendered pages; CORS in `main.py` allows those origins.
- **No token issuance** — launch tokens are minted by the portal backend; this service only verifies and relays them.
- **No test suite** — pre-commit (black/flake8) is the only automated check; verification is manual via local server + `?debug=true`.
- **No DB migrations** — DynamoDB tables, Mongo collections, and BigQuery datasets are provisioned outside this repo.
