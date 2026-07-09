---
name: agents
description: Always-loaded project anchor. Read this first. Contains project identity, non-negotiables, commands, and pointer to ROUTER.md for full context.
last_updated: 2026-07-09
---

# Avanti Fellows Reporting Engine

## What This Is
A FastAPI service (deployed as an AWS Lambda) that renders student quiz reports, live session reports, and form-response reports as HTML/PDF from DynamoDB, MongoDB, BigQuery, and Firestore data.

## Non-Negotiables
- Never use `app.`-prefixed imports — the server runs from inside `app/` (`from db.reports_db import ...`)
- All data-source queries go through `app/db/` wrapper classes, never raw clients in routers
- Every report endpoint supports `?format=pdf` + `debug` via `convert_template_to_pdf`
- Never commit secrets; new env vars must land in `.env.example` + both SAM templates + both deploy workflows
- Guard numeric template fields against `None` (DynamoDB NULLs crash Jinja `format` filters)

## Commands
- Dev: `cd app && uv run uvicorn main:app --port 5050 --reload`
- Lint/format: `uv run pre-commit run --all-files`
- Deps: `uv sync` / `uv add <package>`
- Drift check: `mex check`

## Scaffold Growth
After meaningful work, run GROW:
- Ground: what changed in reality?
- Record: update `ROUTER.md` and relevant `context/` files
- Orient: create or update a `patterns/` runbook if this can recur
- Write: bump `last_updated` on changed scaffold files and run `mex log` when rationale matters

## Navigation
At the start of every session, read `ROUTER.md` before doing anything else.
For full project context, patterns, and task guidance — everything is there.
