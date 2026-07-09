---
name: setup
description: Dev environment setup and commands. Load when setting up the project for the first time or when environment issues arise.
triggers:
  - "setup"
  - "install"
  - "environment"
  - "getting started"
  - "how do I run"
  - "local development"
edges:
  - target: context/stack.md
    condition: when specific technology versions or library details are needed
  - target: patterns/debug-local-startup.md
    condition: when the server fails to start or crashes at import time
last_updated: 2026-07-09
---

# Setup

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Credentials for DynamoDB, MongoDB Atlas, Firestore, and AWS Secrets Manager (obtain from repository owners)

## First-time Setup

1. `uv sync` — install dependencies and create the virtualenv
2. `uv run pre-commit install` — install git hooks (black, flake8, whitespace/JSON/YAML checks)
3. `cp .env.example .env.local` and fill in real credentials
4. Add `PORTAL_BACKEND_URL` to `.env.local` — it is **missing from `.env.example`** but required at import time
5. `cd app && uv run uvicorn main:app --port 5050 --reload` — the server **must be run from inside `app/`** (imports, templates, and static paths are relative to it)
6. Open http://localhost:5050/docs

## Environment Variables

Required (server won't start or won't serve reports without them):
- `DYNAMODB_URL`, `DYNAMODB_REGION`, `DYNAMODB_ACCESS_KEY`, `DYNAMODB_SECRET_KEY` — DynamoDB connection
- `MONGO_AUTH_CREDENTIALS` — MongoDB Atlas connection string
- `FIRESTORE_CREDENTIALS` — **base64-encoded** service-account JSON (decoded in `app/db/sessions_db.py`)
- `BQ_CREDENTIALS_SECRET_NAME` — AWS Secrets Manager secret holding the BigQuery service-account JSON (fetching it also needs working AWS credentials)
- `PORTAL_BACKEND_URL` — portal backend base URL; read via `os.environ[...]` at import of `app/auth/__init__.py`, so a missing value is a `KeyError` crash at startup

Conditional / feature-specific:
- `HTML_TO_PDF_SERVER_URL` — required for `?format=pdf` (note: the SAM templates call the parameter `HtmlToPdfUrl`; the runtime env var is `HTML_TO_PDF_SERVER_URL`)
- `OPENROUTER_API_KEY` — required for form-response LLM summaries

Legacy / unused in code:
- `DYNAMODB_STUDENT_REPORTS_TABLE_NAME` — in `.env.example` but table names are hard-coded in `app/db/reports_db.py`
- `OPENAI_API_KEY` — superseded by OpenRouter

## Common Commands

- `cd app && uv run uvicorn main:app --port 5050 --reload` — dev server with hot reload
- `uv run pre-commit run --all-files` — all quality checks (black, flake8, misc hooks)
- `uv run pre-commit run black` / `uv run pre-commit run flake8` — individual hooks
- `uv sync --upgrade` — update dependencies
- `uv add <package>` / `uv add --dev <package>` — add a dependency
- `mex check` — scaffold drift score for this memory system

## Common Issues

**`KeyError: 'PORTAL_BACKEND_URL'` at startup:** the variable is read at module import and isn't in `.env.example`. Add it to `.env.local`. It loads only because `internal.db`'s `load_dotenv("../.env.local")` runs before `auth` is imported in `main.py` — don't reorder those imports.

**`TypeError`/base64 errors from `SessionsDB.__init__` at startup:** `FIRESTORE_CREDENTIALS` must be the base64 of the service-account JSON, not the raw JSON.

**Templates or static files not found:** you ran uvicorn from the repo root. `Jinja2Templates(directory="templates")` and `StaticFiles(directory="static")` resolve relative to the working directory — run from inside `app/`.

**PDF endpoint returns "Error generating PDF" locally:** `HTML_TO_PDF_SERVER_URL` is unset or unreachable. Use `?format=pdf&debug=true` to get the inlined HTML instead and verify the report itself.
