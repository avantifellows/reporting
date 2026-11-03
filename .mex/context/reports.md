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
last_updated: 2026-11-03
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

## Cumulative report (GET `/reports/cumulative_report/{user_id}`)

- Built only from the student's v2 docs (`get_student_reports_v2`, paginated). Logic in `app/utils/cumulative_report.py`; template `student_cumulative_report.html` (one template for screen, print and PDF; CSS is the approved "AIAT student report" design, JEE and NEET variants).
- Test pick: last 3 (min 2) with `test_format` in major/full_syllabus/mock/part, `has_quiz_ended` not False, name without "baseline"/"advance", the G11/G12 in the name equal to the student's grade, same stream as the latest big test; a repeated test name keeps the later sitting. Fewer than 2 -> `error.html`.
- Question counts are right + wrong + partial + skipped: v2 subject `total_questions` holds the whole paper's count (75 JEE / 180 NEET). Root cause: the quiz ETL Lambda stamps the quiz's question count on every row; fixed in etl-next `stg_test_results` (branch `fix/subject-total-questions`, 2026-11-03), but existing v2 docs keep the old value until re-emitted, so keep summing.
- Chapters are summed across tests by (subject, name). Old-system names ("12C20 - Electrochemistry") have the code prefix stripped so exact-name matches merge and take the current priority; other old chapters have no priority and drop out of the High-only tables. Every chapter is listed (no cap), on the web and in the PDF. JEE stays at 2 A4 pages; NEET runs to 3 (page 2 is allowed to grow; each subject table is kept whole). "What to do next" sits at the top of page 2.
- Launch-token cookie prefix `cumulative_report_launch`, cookie path `/reports/cumulative_report`. PDF calls `convert_template_to_pdf(..., default_css=False)` so the converter's fallback CSS doesn't override the template.
- Not built: NEET AF ranks and mentor names from the spec; Gurukul button (its `launchPath.ts` only knows per-test report paths).

## Gotchas

- **None-guard numeric fields**: v2 upstream stores DynamoDB NULL for `percentage`/`accuracy` when a subject is fully skipped; `render_v2_report` zeroes them before the template's `format` filters. Extend `_NUMERIC_FIELDS` if templates start formatting new numeric attributes.
- `session_id`/`user_id` arrive URL-encoded — always `unquote` before querying.
- v1 wrapper methods raise `ValueError` (wrapping `ClientError`) on single-report lookups but return `[]` from listing methods — routers rely on both behaviors.
- Table names are hard-coded in `ReportsDB`; there is no staging DynamoDB table (staging points at prod data unless overridden).
- `QUIZ_AF_API_KEY` in `app/routers/student_quiz_reports.py` is a hard-coded, publicly visible key for quiz.avantifellows.org handoff links.
- **Form responses (`form_question_responses`)**: the viewer skips rows with `was_displayed` False (a conditional follow-up the student was not shown) before numbering, counting `total_questions` and building the AI-summary input, and shows `Other: <other_text>` for a single-choice-other answer. Rows without those fields render as before. As of 2026-10-21 nothing writes this table (the quiz ETL's DynamoDB upload was disabled in etl-data-flow `46e7610`; zero writes since 2026-05-31), so new forms show "No report found"; whoever re-enables the writer must store `was_displayed` (BOOL) and `other_text`.
