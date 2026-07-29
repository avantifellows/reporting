---
name: add-db-query
description: Adding a query method to a DB wrapper class (DynamoDB, MongoDB, BigQuery, or Firestore).
triggers:
  - "db query"
  - "dynamodb"
  - "mongo"
  - "bigquery"
  - "firestore"
edges:
  - target: context/architecture.md
    condition: to see which wrapper owns which data source
  - target: context/reports.md
    condition: when querying the report tables — key schemas live there
last_updated: 2026-07-09
---

# Add a DB Query

## Context

All queries live in `app/db/` wrapper classes; routers only call wrapper methods. Each wrapper holds its client as `self.__db`/`self.__client` (constructor-injected from `app/main.py`, except `SessionsDB` which builds its own Firestore client).

## Steps

1. Add a method to the right wrapper: `ReportsDB`/`FormResponsesDB` (DynamoDB), `QuizDB` (Mongo), `BigQueryDB`, `SessionsDB` (Firestore).
2. DynamoDB: get the table with `self.__db.Table("<hard-coded name>")`, build conditions with `boto3.dynamodb.conditions.Key`, wrap in try/except on `ClientError` — raise `ValueError(e.response["Error"]["Message"])` for single-item lookups, return `[]` for listings.
3. Mongo: use aggregation pipelines on `self.__db.quiz.<collection>`; time-range filtering is done by generating ObjectIds via `ObjectId.from_datetime` and comparing on `_id`.
4. BigQuery: inline SQL string, `list(self.__client.query(q).result())`, and return a safe-default dict on any exception (reports must degrade, not 500).
5. Return plain dicts/lists — no Pydantic models.

## Gotchas

- DynamoDB table names are **hard-coded** in the wrappers (`student_quiz_reports`, `student_quiz_reports_v2`); the `DYNAMODB_STUDENT_REPORTS_TABLE_NAME` env var is a red herring.
- Queries with `FilterExpression` can return empty pages while more data exists — paginate with `LastEvaluatedKey` (see `get_student_quiz_report_v2_by_alt_id`).
- BigQuery SQL is built with f-strings from URL path params — keep inputs to identifiers you've validated; prefer parameterized queries for anything new.
- DynamoDB numbers come back as `Decimal` and NULLs as `None` — templates must be guarded (see `context/reports.md`).

## Verify

- [ ] Method sits in the wrapper, router only calls it
- [ ] Error path returns `[]`/default dict or raises `ValueError` — consistent with siblings
- [ ] Tested against real data locally (hit the endpoint or call the method in `uv run python` from `app/`)

## Debug

- `ClientError: ResourceNotFoundException` → wrong table name or wrong DynamoDB endpoint/region in `.env.local`
- Empty results for a user you know exists → v1 keys are `"{user_id}#{section}"`; check you're not querying v1 shape against v2 or vice versa

## Update Scaffold

- [ ] Update `context/reports.md` if a table/schema detail changed
- [ ] Update `.mex/ROUTER.md` project state if a new data source was added
