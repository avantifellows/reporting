# Combined student reports — the af_lms ↔ reporting contract

The seam between the two repos for the `reports-ui` task. **af_lms** is the front door (button on the
school page + a job view in the Performance tab); **reporting** runs the async job. Keep this file in
sync if either side changes — it is the single source of truth for the wire format.

Per-task scope lives in `~/af/worklog/tasks/reports-ui.md`.

## Flow

```
af_lms (school page)                 reporting (Lambda)                  reporting worker (SQS Lambda)
  │  POST /reports/combined  ───────▶ validate X-Api-Key
  │  {session_id, school, students}   write report_jobs (queued)
  │                                   enqueue SQS {job_id}  ───────────▶ load job, status=processing
  │  ◀── {job_id, status:queued}                                         read student_quiz_reports_v2
  │                                                                      by session_id, filter→roster
  │  GET /reports/combined/{job_id}                                      render each (jinja→html_to_pdf)
  │     (poll)              ◀──────── job record (status, download_url)  pypdf merge → S3
  │                                                                      status=done (or errored)
  │  POST /reports/combined/{job_id}/retry  ──▶ re-enqueue
```

## Auth

af_lms's **server** (never the browser) calls reporting with a shared service key:

```
X-Api-Key: <REPORTING_SERVICE_API_KEY>
```

reporting validates it against its `REPORTING_SERVICE_API_KEY` env (constant-time compare). The user is
already authenticated + authorized for the school by af_lms (`authorizeSchoolAccess(udise)`), so reporting
trusts the caller and does not re-verify the end user. This mirrors the gurukul→reporting api-key edge.

## 1. Submit — `POST /reports/combined`

Request body:

```jsonc
{
  "session_id": "EnableStudents_68b6e2ea88ea453ce18f3566",  // required; the test/session
  "test_name":  "JEE G12 CCT2",                              // optional; label only
  "school": {
    "udise": "29010100123",                                 // required (≥1 of udise/code)
    "code":  "JNV-WRD",
    "name":  "JNV Wardha"
  },
  "students": [                                              // required; af_lms roster for this school
    { "user_id": "1403899", "student_id": "AF12345", "apaar_id": "" },
    ...                                                       // ~50–60 for a physical centre
  ],
  "requested_by": "teacher@avantifellows.org"               // optional; audit only
}
```

- `students` is af_lms's authoritative current-year roster (`getSchoolRoster`). reporting filters the
  session's v2 records to this set by a **3-way id match** (a v2 doc is kept if its `user_id`, `student_id`,
  or non-empty `apaar_id` matches any roster entry). This replaces the old `metadata.school` string filter.
- Every id may be sent as a string; reporting compares as strings.

Response `202`:

```json
{ "job_id": "b1c2…", "status": "queued" }
```

## 2. Poll — `GET /reports/combined/{job_id}`

Returns the job record (see schema). When `status == "done"`, `download_url` is a **freshly-generated**
presigned S3 URL (regenerated each poll, ~1h expiry — never stored stale).

```json
{
  "job_id": "b1c2…",
  "session_id": "EnableStudents_…",
  "school_code": "JNV-WRD",
  "test_name": "JEE G12 CCT2",
  "status": "done",
  "student_count": 58,
  "matched_count": 55,
  "missing_count": 3,
  "error": null,
  "download_url": "https://…s3…/…?X-Amz-Signature=…",
  "created_at": "2026-06-23T18:04:11Z",
  "updated_at": "2026-06-23T18:05:02Z",
  "retry_count": 0
}
```

`matched_count`/`missing_count` let the UI say "55 of 58 students had reports for this test".

## 3. List (Performance-tab view) — `GET /reports/combined?session_id=…&school_code=…`

Returns `{ "jobs": [ <record>, … ] }` most-recent-first, for that session+school. Drives the
"reports generated for this test" list with status chips + retry/download.

## 4. Retry — `POST /reports/combined/{job_id}/retry`

Only valid when `status == "errored"`. Resets to `queued`, bumps `retry_count`, re-enqueues. Returns the job.

## Status lifecycle (teacher-visible)

`queued → started → processing → done` | `errored` (retryable).
- `queued` — job written, SQS message sent.
- `started` — worker picked it up.
- `processing` — rendering/merging.
- `done` — combined PDF in S3; `download_url` available.
- `errored` — `error` holds a short message; retry allowed.

## DynamoDB `report_jobs` table

- **PK** `job_id` (S, uuid4).
- **GSI `session_school_index`**: PK `session_school` (S, `"{session_id}#{school_code}"`), SK `created_at` (S, ISO8601) — powers the List query.
- Attributes: `session_id`, `school_code`, `school_udise`, `school_name`, `test_name`, `status`,
  `student_count`, `matched_count`, `missing_count`, `students` (L of M — the roster, read by the worker),
  `requested_by`, `error`, `s3_key`, `retry_count`, `created_at`, `updated_at`.

## S3

- Bucket: `REPORTS_S3_BUCKET` env.
- Key: `combined-reports/{session_id}/{school_code}/{job_id}.pdf` (job_id keys the object → no
  same-test-name collision).
- Download via presigned GET generated on poll.

## Source of report content

The worker reads per-student **AIET v2.0** docs from `student_quiz_reports_v2` (PK `session_id`, SK
`user_id`) — these already carry `report_header` / `overall_performance` / `subject_performance` /
`chapter_performance` / `recommendation`, i.e. the Jinja template's input. **No BigQuery in the worker.**
A test only appears in af_lms's Performance tab if its v2 records exist, so the data is guaranteed present.
