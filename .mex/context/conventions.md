---
name: conventions
description: How code is written in this project — naming, structure, patterns, and style. Load when writing new code or reviewing existing code.
triggers:
  - "convention"
  - "pattern"
  - "naming"
  - "style"
  - "how should I"
  - "what's the right way"
edges:
  - target: context/architecture.md
    condition: when a convention depends on understanding the system structure
  - target: patterns/add-report-endpoint.md
    condition: when adding a new endpoint — the full workflow lives there
last_updated: 2026-07-09
---

# Conventions

## Naming

- Files and functions: snake_case (`student_quiz_reports.py`, `get_student_quiz_report`)
- Classes: PascalCase with a role suffix — routers end in `Router` (`StudentQuizReportsRouter`), DB wrappers end in `DB` (`ReportsDB`, `QuizDB`)
- Endpoint functions are verb-first or noun descriptors matching the URL (`get_student_reports`, `student_quiz_report`)
- Private state uses double-underscore name mangling (`self.__reports_db`); templates attr is single underscore (`self._templates`)
- Jinja templates named after the endpoint/report they render (`student_quiz_report_v2.html`, `_print` suffix for the PDF variant)

## Structure

- **Imports have no `app.` prefix** — the server runs from inside `app/` (`cd app && uv run uvicorn main:app`), so it's `from db.reports_db import ReportsDB`, never `from app.db...`. Getting this wrong breaks Lambda too.
- Routers are classes in `app/routers/`, one per report family; endpoints are closures inside the `router` `@property`, and helper functions private to a router live as `_`-prefixed closures in the same property
- All data-source queries live in `app/db/` wrapper classes — never call boto3/pymongo/bigquery clients from a router
- Clients are created once in `app/main.py` (via `app/internal/db.py`) and injected into router constructors; routers never build their own clients
- Templates in `app/templates/`, static assets in `app/static/` (mounted at `/static`)

## Patterns

Report endpoints all follow the same response contract — accept optional `format` and `debug` query params, render a template, and route PDF requests through the converter:

```python
template_response = self._templates.TemplateResponse(
    "some_report.html", {"request": request, "report_data": report_data}
)
if format == "pdf":
    return convert_template_to_pdf(template_response, debug=debug)
return template_response
```

Path params arriving from URLs are decoded before use:

```python
session_id = unquote(session_id)
user_id = unquote(user_id)
```

DynamoDB wrapper methods catch `ClientError` and either re-raise as `ValueError` (single-item lookups the router handles) or return `[]` (list endpoints degrade gracefully):

```python
except ClientError as e:
    raise ValueError(e.response["Error"]["Message"])
```

Token-protected endpoints come in pairs — a `{session_id}`-only route that resolves the user from a launch token (redirecting to set a cookie first), delegating to the plain `{session_id}/{user_id}` route. See `context/auth.md`.

Guard numeric fields against `None` before templates apply `format` filters — DynamoDB stores NULL for undefined metrics (e.g. accuracy on a fully-skipped subject) and `"%.1f"|format(None)` raises:

```python
if report["overall_performance"].get("accuracy") is None:
    report["overall_performance"]["accuracy"] = 0
```

## Verify Checklist

Before presenting any code:
- [ ] No `app.` prefix in imports; code works when run from inside `app/`
- [ ] DB queries are in an `app/db/` wrapper, not in the router
- [ ] Report endpoints support `format=pdf` + `debug` and route through `convert_template_to_pdf`
- [ ] URL path params are `unquote`d before querying
- [ ] Numeric template fields are None-guarded before `format` filters
- [ ] New env vars added to `.env.example`, both SAM templates (`templates/staging.yaml`, `templates/prod.yaml`), and both deploy workflows
- [ ] `uv run pre-commit run --all-files` passes (black + flake8)
