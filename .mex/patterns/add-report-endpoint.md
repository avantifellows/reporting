---
name: add-report-endpoint
description: Adding a new report endpoint (HTML + PDF + optional launch-token support) to an existing or new router class.
triggers:
  - "add endpoint"
  - "new report"
  - "new route"
edges:
  - target: context/conventions.md
    condition: always — the response contract and import rules live there
  - target: context/auth.md
    condition: if the endpoint should support launch tokens
  - target: patterns/add-db-query.md
    condition: if the endpoint needs a new data query
last_updated: 2026-07-09
---

# Add a Report Endpoint

## Context

Read `context/conventions.md` (response contract, import rules) and skim an existing router — `app/routers/session_quiz_reports.py` is the smallest example. Routers are classes; endpoints are closures inside the `router` `@property`.

## Steps

1. Pick the router class in `app/routers/` (or create one mirroring `SessionQuizReportsRouter`: constructor takes DB wrappers, `router` property builds `APIRouter(prefix="/reports", tags=[...])`).
2. Define the endpoint closure with `request: Request`, path params, and the standard `format: Optional[str] = None, debug: bool = False` query params.
3. `unquote()` any path params that can contain encoded characters.
4. Query through an `app/db/` wrapper method — never a raw client. Add the method if missing (see `patterns/add-db-query.md`).
5. Build the context dict and render a Jinja template from `app/templates/` (create it extending `layout.html` if new).
6. Close with the standard contract: `if format == "pdf": return convert_template_to_pdf(template_response, debug=debug)` else return the template response.
7. For launch-token support, add the paired `{session_id}`-only route that calls `redirect_with_launch_cookie` / `get_report_launch_token` / `resolve_report_user_id` with a **unique cookie_prefix**, then delegates to the explicit-user route (copy the shape from `student_quiz_report_with_token`).
8. If it's a new router class: instantiate it in `app/main.py` with its DB wrappers and `app.include_router(...)`.

## Gotchas

- Route ordering matters: a literal path like `/student_quiz_report/v3/{session_id}` must be declared so it isn't swallowed by `/student_quiz_report/{session_id}/{user_id}` — check with `/docs` that the right handler matches.
- No-data cases render `error.html` with an `error_data` dict, not a raised 404 (users see a friendly page).
- None-guard numeric fields before templates `format` them (DynamoDB NULLs).
- New template + CSS: PDF conversion inlines `app/static/style.css` only — styles in other files won't reach the PDF.

## Verify

- [ ] `cd app && uv run uvicorn main:app --port 5050 --reload` starts clean
- [ ] Endpoint appears in http://localhost:5050/docs and returns HTML
- [ ] `?format=pdf&debug=true` returns inlined HTML (CSS present in `<style>` tag)
- [ ] No-data path renders `error.html`, doesn't 500
- [ ] `uv run pre-commit run --all-files` passes

## Debug

- 500 at startup → import-time env var problem, see `patterns/debug-local-startup.md`
- Template not found → server not running from `app/`
- Empty report → check the DB wrapper directly in a REPL; verify key format (`"{user_id}#{section}"` for v1)

## Update Scaffold

- [ ] Update `.mex/ROUTER.md` "Current Project State" if what's working/not built has changed
- [ ] Update `context/reports.md` if a new report family or schema was added
- [ ] If this introduced a new task type, add a pattern and INDEX row
