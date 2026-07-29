---
name: router
description: Session bootstrap and navigation hub. Read at the start of every session before any task. Contains project state, routing table, and behavioural contract.
edges:
  - target: context/architecture.md
    condition: when working on system design, integrations, or understanding how components connect
  - target: context/stack.md
    condition: when working with specific technologies, libraries, or making tech decisions
  - target: context/conventions.md
    condition: when writing new code, reviewing code, or unsure about project patterns
  - target: context/decisions.md
    condition: when making architectural choices or understanding why something is built a certain way
  - target: context/setup.md
    condition: when setting up the dev environment or running the project for the first time
  - target: context/reports.md
    condition: when working on report schemas, the v1/v2/v3 lookup chain, or report templates
  - target: context/auth.md
    condition: when working on launch tokens, cookies, or report access control
  - target: patterns/INDEX.md
    condition: when starting a task — check the pattern index for a matching pattern file
last_updated: 2026-07-09
---

# Session Bootstrap

If you haven't already read `AGENTS.md`, read it now — it contains the project identity, non-negotiables, and commands.

Then read this file fully before doing anything else in this session.

## Current Project State

**Working:**
- Student quiz reports: v2 (primary, refreshed UI + print/PDF variant), v1 fallback, v3 (BigQuery-enriched with chapter recommendations)
- Launch-token auth flow (portal-verified, cookie handoff) across quiz reports and form responses, plus quiz-review handoff links
- Live session / live quiz reports from Mongo aggregation + Firestore session lookup
- Form responses with OpenRouter LLM theme summaries
- PDF generation via external HTML-to-PDF service; staging + prod deploys via GitHub Actions + SAM

**Not yet built:**
- Test suite (no tests exist; pre-commit black/flake8 is the only automated check)
- Staging DynamoDB table (staging reads prod-shaped data; flagged as pending work in a comment in `app/internal/db.py`)
- Firestore Sessions → Postgres migration (Firestore is explicitly temporary)

**Known issues:**
- `PORTAL_BACKEND_URL` missing from `.env.example` despite being required at import time
- `DYNAMODB_STUDENT_REPORTS_TABLE_NAME` env var is unused — table names are hard-coded in `app/db/reports_db.py`
- BigQuery queries interpolate URL params into f-string SQL (`app/db/bq_db.py`)
- `api_key_header` on the student-reports listing is decorative — endpoint is effectively public

## Routing Table

Load the relevant file based on the current task. Always load `context/architecture.md` first if not already in context this session.

| Task type | Load |
|-----------|------|
| Understanding how the system works | `context/architecture.md` |
| Working with a specific technology | `context/stack.md` |
| Writing or reviewing code | `context/conventions.md` |
| Making a design decision | `context/decisions.md` |
| Setting up or running the project | `context/setup.md` |
| Report schemas, v1/v2/v3 lookup, report templates | `context/reports.md` |
| Launch tokens, cookies, access control | `context/auth.md` |
| Any specific task | Check `patterns/INDEX.md` for a matching pattern |

## Behavioural Contract

For every task, follow this loop:

1. **CONTEXT** — Load the relevant context file(s) from the routing table above. Check `patterns/INDEX.md` for a matching pattern. If one exists, follow it. Narrate what you load: "Loading architecture context..."
2. **BUILD** — Do the work. If a pattern exists, follow its Steps. If you are about to deviate from an established pattern, say so before writing any code — state the deviation and why.
3. **VERIFY** — Load `context/conventions.md` and run the Verify Checklist item by item. State each item and whether the output passes. Do not summarise — enumerate explicitly.
4. **DEBUG** — If verification fails or something breaks, check `patterns/INDEX.md` for a debug pattern. Follow it. Fix the issue and re-run VERIFY.
5. **GROW** — After meaningful work, run this binary checklist:
   - **Ground:** What changed in reality? Name the changed behavior, system, command, dependency, or workflow.
   - **Record:** If project state changed, update the "Current Project State" section above. If documented facts changed, update the relevant `context/` file surgically.
   - **Orient:** If this task can recur and no pattern exists, create one in `patterns/` using `patterns/README.md`, then add it to `patterns/INDEX.md`. If a pattern exists but you learned a gotcha, update it.
   - **Write:** Bump `last_updated` in every scaffold file you changed. If the why matters, run `mex log --type decision "<what changed and why>"` or `mex log "<note>"`.
