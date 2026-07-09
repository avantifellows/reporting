---
name: decisions
description: Key architectural and technical decisions with reasoning. Load when making design choices or understanding why something is built a certain way.
triggers:
  - "why do we"
  - "why is it"
  - "decision"
  - "alternative"
  - "we chose"
edges:
  - target: context/architecture.md
    condition: when a decision relates to system structure
  - target: context/stack.md
    condition: when a decision relates to technology choice
  - target: context/reports.md
    condition: when a decision relates to report schemas or the v1/v2 split
last_updated: 2026-07-09
---

# Decisions

## Decision Log

### Read-only polyglot persistence
**Date:** 2022-07-27 (repo inception)
**Status:** Active
**Decision:** This service reads from whichever store each upstream system owns — DynamoDB for reports, MongoDB for quiz sessions, Firestore for session metadata, BigQuery for analytics — rather than consolidating into one database.
**Reasoning:** The reporting engine is a presentation layer over data produced elsewhere; owning a copy would mean building and operating sync pipelines.
**Alternatives considered:** Single warehouse (rejected — reports must reflect live quiz state; ETL delay unacceptable for live session reports).
**Consequences:** Four client initializations at startup; local dev needs credentials for all four; a failure in any one source degrades only its report family.

### v2 report schema in a separate DynamoDB table with v1 fallback
**Date:** 2026-04 (v2 UI refresh, PR #76)
**Status:** Active
**Decision:** New-format reports live in `student_quiz_reports_v2` (single item per user+session with nested `report_header`/`overall_performance`/`subject_performance`); the old `student_quiz_reports` (item per user+section) stays. Lookup tries v2, then v2 by alt-id (`student_id`/`apaar_id`), then v1.
**Reasoning:** Old reports could not be migrated; two schemas must coexist indefinitely. Separate tables avoid polluting one table with two shapes.
**Alternatives considered:** In-place schema versioning on the v1 table (rejected — v1 spreads one report across many items keyed by `user_id-section`, incompatible with the v2 single-item shape).
**Consequences:** Every report-fetch path must handle both schemas; the reports listing merges v1+v2, preferring v2 for duplicate session_ids. See `context/reports.md`.

### Launch-token auth verified by the portal backend
**Date:** 2026-04-22 ("Support report launch tokens")
**Status:** Active
**Decision:** Reports opened from the quiz/portal carry a `?launchToken=` that this service verifies by calling the portal backend's auth-verify endpoint (`PORTAL_BACKEND_URL` + "/auth/verify"); the token is moved into a scoped, httponly, 15-minute cookie via a 302 redirect that strips it from the URL.
**Reasoning:** Keeps a single source of truth for identity (portal backend), removes user_id guessing from tokenless URLs, and keeps tokens out of shareable/bookmarkable URLs.
**Alternatives considered:** Verifying JWTs locally with a shared secret (rejected — portal owns session semantics like `session_mode` and audience); passing user_id in the URL only (still supported for direct links, but provides no identity guarantee).
**Consequences:** `PORTAL_BACKEND_URL` is required at import time (`app/auth/__init__.py` reads `os.environ[...]` at module load). The verified token is also reused to build the quiz-review handoff link. See `context/auth.md`.

### External HTML-to-PDF service instead of rendering PDFs in-process
**Date:** ~2023 (PDF support), current form since the pdf_converter rewrite
**Status:** Active
**Decision:** `?format=pdf` inlines CSS/images into the rendered HTML and POSTs it to `HTML_TO_PDF_SERVER_URL`; the PDF is streamed back to the client.
**Reasoning:** Running headless Chrome inside this Lambda is heavy and fragile; a dedicated service isolates that concern.
**Alternatives considered:** pyppeteer in-process (the dependency is still in `pyproject.toml` but unused).
**Consequences:** PDFs need the external service reachable; `?debug=true` returns the inlined HTML instead, which is the standard way to debug PDF issues locally.

### LLM summaries via OpenRouter, not OpenAI directly
**Date:** 2026-01-30 ("Switch from OpenAI to OpenRouter for LLM summaries")
**Status:** Active
**Decision:** Form-response theme summaries use the OpenAI SDK pointed at OpenRouter (base_url https://openrouter.ai/api/v1), model "google/gemini-3-flash-preview".
**Reasoning:** OpenRouter allows model flexibility/cost control without changing the SDK integration.
**Alternatives considered:** OpenAI API directly (superseded — the original integration).
**Consequences:** `OPENROUTER_API_KEY` required for form-response summaries; summaries fail soft (return `None`, logged) so reports still render.

### Deploy as a single Lambda behind API Gateway via AWS SAM
**Date:** 2022 (repo inception)
**Status:** Active
**Decision:** The whole FastAPI app deploys as one Lambda (Mangum adapter), provisioned by SAM templates (`templates/staging.yaml`, `templates/prod.yaml`) through GitHub Actions.
**Reasoning:** Spiky, low-baseline traffic (reports are viewed after tests); serverless avoids idle servers and manual AWS console work.
**Alternatives considered:** Long-running container/EC2 (rejected — cost and ops for bursty traffic).
**Consequences:** Cold starts include all four DB client initializations; env vars must be declared in both SAM templates and both workflows; static assets are served from the Lambda itself.
