---
name: stack
description: Technology stack, library choices, and the reasoning behind them. Load when working with specific technologies or making decisions about libraries and tools.
triggers:
  - "library"
  - "package"
  - "dependency"
  - "which tool"
  - "technology"
edges:
  - target: context/decisions.md
    condition: when the reasoning behind a tech choice is needed
  - target: context/conventions.md
    condition: when understanding how to use a technology in this codebase
  - target: context/setup.md
    condition: when installing or configuring any of these technologies locally
last_updated: 2026-07-09
---

# Stack

## Core Technologies

- **Python 3.11+** (`requires-python = ">=3.11"`; Lambda runtime is Python 3.11)
- **FastAPI** — web framework; endpoints are mostly sync `def` (only form responses use `async`)
- **Mangum** — ASGI-to-Lambda adapter; `handler = Mangum(app)` in `app/main.py` is the Lambda entry point
- **uv** — package manager and virtualenv tool; all dev commands run through `uv run`
- **Jinja2** — server-side HTML templates in `app/templates/`, shared CSS in `app/static/style.css`

## Key Libraries

- **boto3** — DynamoDB access (`app/db/reports_db.py`, `form_responses_db.py`) and Secrets Manager (BigQuery creds); use `boto3.dynamodb.conditions.Key` for key expressions
- **pymongo** — MongoDB Atlas; live-stats queries are aggregation pipelines, and time filtering is done by generating ObjectIds from datetimes (`ObjectId.from_datetime`)
- **google-cloud-bigquery / google-cloud-firestore** — BigQuery client built from a Secrets Manager JSON key; Firestore client from base64-encoded `FIRESTORE_CREDENTIALS`
- **openai SDK pointed at OpenRouter** (not the OpenAI API) — `AsyncOpenAI(base_url="https://openrouter.ai/api/v1")`, model "google/gemini-3-flash-preview"
- **httpx** — sync calls to the portal backend for token verification (`app/auth/__init__.py`); **requests** — POST to the HTML-to-PDF service
- **BeautifulSoup4** — rewrites report HTML before PDF conversion (inline CSS, base64 images)
- **black + flake8 via pre-commit** — formatting and linting (E501, E203, W503 ignored)

## What We Deliberately Do NOT Use

- **No ORM / ODM** — raw boto3 table calls, raw pymongo pipelines, raw SQL strings for BigQuery; queries stay inside `app/db/` wrappers
- **No local headless browser for PDFs** — HTML is sent to an external HTML-to-PDF service (`pyppeteer` is in the dependency list but unused at runtime); Lambda can't comfortably run Chrome
- **No Pydantic request/response models in routes** — endpoints take plain path/query params and return template responses or dicts; `app/models/` is documentation-only, not used at runtime
- **No test framework in practice** — there is no tests/ directory; don't invent pytest suites without discussing first

## Version Constraints

- Lambda runs **Python 3.11** — don't use 3.12+-only syntax.
- `urllib3>=1.26.20` is pinned below 2.x territory by boto3/botocore compatibility; be careful bumping it.
