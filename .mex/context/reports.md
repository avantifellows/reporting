---
name: reports
description: Report data schemas (v1/v2/v3), the DynamoDB lookup chain, and template mapping. Load when working on any student quiz report endpoint or template.
triggers:
  - "student quiz report"
  - "v1 report"
  - "v2 report"
  - "v3 report"
  - "report schema"
  - "chapter"
  - "percentile"
edges:
  - target: context/architecture.md
    condition: when the wider request flow around reports is needed
  - target: context/auth.md
    condition: when the report is accessed via launch token
  - target: patterns/add-report-endpoint.md
    condition: when adding or modifying a report endpoint
last_updated: 2026-07-09
---

# Report Schemas & Lookup

## v1 — `student_quiz_reports` (DynamoDB)

- One item **per user per section**: PK `session_id`, SK `user_id-section` formatted as `"{user_id}#{section}"`; GSI `gsi_user_id` on `user_id`.
- Sections: `overall` plus subject sections; items carry metrics (`marks_scored`, `num_correct`, `percentile`, `rank`, …) and optional `chapter_wise_data`.
- Fetch: `ReportsDB.get_student_quiz_report(user_id, session_id)` — a `begins_with(f"{user_id}#")` query returning all section items.
- Rendered by `app/templates/student_quiz_report.html`; display names for metrics come from `ROW_NAMES` / `CHAPTER_WISE_ROW_NAMES` in `app/routers/student_quiz_reports.py`.

## v2 — `student_quiz_reports_v2` (DynamoDB)

- One item **per user per session**: PK `session_id` + `user_id`; GSI `user_id_index`. Nested dicts: `report_header`, `overall_performance`, `subject_performance`, plus `student_id` / `apaar_id` attributes.
- Rendered by `app/templates/student_quiz_report_v2.html` (display) or `student_quiz_report_v2_print.html` (for `?print=true` and PDFs).
- Quiz review link: built from `quiz_id`/`test_id` on the item, else derived from the session_id suffix (`session_id.rsplit("_", 1)[-1]`), and only when a verified launch token is on the request.

## Lookup chain (GET `/reports/student_quiz_report/{session_id}/{user_id}`)

1. v2 `get_item` by (session_id, user_id)
2. v2 query by session_id partition, filtering `student_id = :id OR (apaar_id = :id AND apaar_id <> "")` — handles logins by alternate identifiers; paginates through `LastEvaluatedKey`
3. v1 section query
4. `error.html` with 404 message

The student reports listing (`/reports/student_reports/{user_id}`) merges both tables — v1 items filtered to `overall` sections, skipping any session_id also present in v2.

## v3 — enrichment on top of v1 (GET `/reports/student_quiz_report/v3/...`)

- Fetches v1 data, then BigQuery `student_profile_al` for `qualification_status`, `marks_to_qualify`, `chapter_curriculum`, `dpp_recommendation` (safe defaults on error).
- Stream detection from item `stream` field: `engineering→JEE`, `medical→NEET`, `ca→CA`, `clat→CLAT` (default JEE). "Advanced" in the test name switches JEE → JEE Advanced messaging; CA/CLAT get no motivational messages.
- Chapters are priority-ordered (High > Medium > Low) using `app/static/chapter_to_links.json`, keyed by chapter code (text before `-` in `chapter_name`), with `Priority_J`/`Priority_N` and `Link_J`/`Link_N` per stream.
- Rendered by `app/templates/student_quiz_report_v3.html`.

## Gotchas

- **None-guard numeric fields**: v2 upstream stores DynamoDB NULL for `percentage`/`accuracy` when a subject is fully skipped; `render_v2_report` zeroes them before the template's `format` filters. Extend `_NUMERIC_FIELDS` if templates start formatting new numeric attributes.
- `session_id`/`user_id` arrive URL-encoded — always `unquote` before querying.
- v1 wrapper methods raise `ValueError` (wrapping `ClientError`) on single-report lookups but return `[]` from listing methods — routers rely on both behaviors.
- Table names are hard-coded in `ReportsDB`; there is no staging DynamoDB table (staging points at prod data unless overridden).
- `QUIZ_AF_API_KEY` in `app/routers/student_quiz_reports.py` is a hard-coded, publicly visible key for quiz.avantifellows.org handoff links.
