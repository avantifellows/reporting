"""
Combined-report worker — a separate, SQS-triggered Lambda (handler
`worker.lambda_handler`). Shares the reporting code bundle but not the FastAPI
app. One SQS message = one job_id.

Per job: load it, walk queued→processing, read the session's AIET v2.0 docs from
DynamoDB, filter to the school roster (3-way id match), render each via the AIET
template + html_to_pdf, merge with pypdf, upload to S3, mark done.

On a processing error we mark the job `errored` and DELETE the message (return
normally) so the user drives retry from the UI — we don't want SQS auto-retrying
a deterministic failure. The queue's redrive policy / DLQ is the backstop for the
truly stuck case (timeout/OOM where we never got to mark errored).
"""

import json

from internal.db import initialize_reports_db
from db.reports_db import ReportsDB
from db.report_jobs_db import ReportJobsDB, STARTED, PROCESSING, DONE, ERRORED
from utils.combined_report import filter_docs_to_roster, build_combined_pdf
from utils.s3_storage import build_key, upload_pdf

# Module-scope init so warm invocations reuse the clients.
_resource = initialize_reports_db()
_reports_db = ReportsDB(_resource)
_jobs_db = ReportJobsDB(_resource)


def _process_job(job_id: str):
    job = _jobs_db.get_job(job_id)
    if not job:
        print(f"[worker] job {job_id} not found; skipping")
        return
    if job.get("status") == DONE:
        print(f"[worker] job {job_id} already done; skipping")
        return

    try:
        _jobs_db.update(job_id, status=STARTED)

        session_id = job["session_id"]
        students = job.get("students") or []

        v2_docs = _reports_db.get_all_session_reports_v2(session_id)
        matched, missing = filter_docs_to_roster(v2_docs, students)

        _jobs_db.update(
            job_id,
            status=PROCESSING,
            matched_count=len(matched),
            missing_count=missing,
        )

        if not matched:
            _jobs_db.update(
                job_id,
                status=ERRORED,
                error="No matching student reports found for this school in this test.",
            )
            return

        pdf_bytes, rendered = build_combined_pdf(matched)
        key = build_key(session_id, job["school_code"], job_id)
        upload_pdf(key, pdf_bytes)

        _jobs_db.update(job_id, status=DONE, s3_key=key, error=None)
        print(f"[worker] job {job_id} done: {rendered} students, key={key}")

    except Exception as e:  # noqa: BLE001 — record any failure as a retryable error
        print(f"[worker] job {job_id} failed: {e}")
        _jobs_db.update(job_id, status=ERRORED, error=str(e)[:500])


def lambda_handler(event, context):
    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
        except (KeyError, ValueError):
            print(f"[worker] bad SQS record, skipping: {record!r}")
            continue
        job_id = body.get("job_id")
        if not job_id:
            print(f"[worker] no job_id in message body: {body!r}")
            continue
        _process_job(job_id)
    return {"ok": True}
