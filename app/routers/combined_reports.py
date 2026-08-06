"""
Combined student-report endpoints (the af_lms front door).

All routes are gated by the service API key (X-Api-Key). af_lms has already
authenticated + authorized the end user for the school; reporting only trusts
the shared secret. See docs/combined-reports-contract.md.
"""

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth.service_key import verify_service_key
from db.report_jobs_db import ReportJobsDB, DONE, ERRORED
from utils.job_queue import enqueue_job
from utils.s3_storage import presigned_url


def _jsonable(obj):
    """DynamoDB returns Decimal; make a job record JSON-serializable."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    return obj


# ---- request models -------------------------------------------------------
class SchoolRef(BaseModel):
    udise: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None


class StudentRef(BaseModel):
    user_id: Optional[str] = None
    student_id: Optional[str] = None
    apaar_id: Optional[str] = None


class CombinedReportRequest(BaseModel):
    session_id: str
    school: SchoolRef
    students: List[StudentRef] = Field(..., min_length=1)
    test_name: Optional[str] = None
    requested_by: Optional[str] = None


# ---- response shaping -----------------------------------------------------
# Fields we don't need to ship back to the UI on every poll (the roster can be
# large). Kept in DynamoDB, dropped from the API response.
_HIDDEN = {"students", "session_school"}


def _present(job: dict) -> dict:
    out = {k: _jsonable(v) for k, v in job.items() if k not in _HIDDEN}
    if job.get("status") == DONE and job.get("s3_key"):
        try:
            out["download_url"] = presigned_url(job["s3_key"])
        except Exception:
            out["download_url"] = None
    else:
        out["download_url"] = None
    return out


class CombinedReportsRouter:
    """Router for combined-report job submit/poll/list/retry."""

    def __init__(self, jobs_db: ReportJobsDB) -> None:
        self.__jobs_db = jobs_db

    @property
    def router(self):
        api_router = APIRouter(
            prefix="/reports/combined",
            tags=["combined-reports"],
            dependencies=[Depends(verify_service_key)],
        )
        jobs_db = self.__jobs_db

        @api_router.post("", status_code=202)
        def submit(payload: CombinedReportRequest):
            if not (payload.school.code or payload.school.udise):
                raise HTTPException(400, "school.code or school.udise is required")
            job = jobs_db.create_job(
                session_id=payload.session_id,
                school=payload.school.model_dump(),
                students=[s.model_dump() for s in payload.students],
                test_name=payload.test_name,
                requested_by=payload.requested_by,
            )
            try:
                enqueue_job(job["job_id"])
            except Exception as e:
                jobs_db.update(job["job_id"], status=ERRORED, error=f"enqueue failed: {e}")
                raise HTTPException(502, "Could not queue the report job")
            return {"job_id": job["job_id"], "status": job["status"]}

        @api_router.get("/{job_id}")
        def get_status(job_id: str):
            job = jobs_db.get_job(job_id)
            if not job:
                raise HTTPException(404, "Job not found")
            return _present(job)

        @api_router.get("")
        def list_jobs(
            session_id: str = Query(...),
            school_code: str = Query(...),
        ):
            jobs = jobs_db.list_jobs(session_id, school_code)
            return {"jobs": [_present(j) for j in jobs]}

        @api_router.post("/{job_id}/retry")
        def retry(job_id: str):
            job = jobs_db.get_job(job_id)
            if not job:
                raise HTTPException(404, "Job not found")
            if job.get("status") != ERRORED:
                raise HTTPException(
                    409, "Only errored jobs can be retried"
                )
            jobs_db.bump_retry(job_id, int(job.get("retry_count") or 0))
            enqueue_job(job_id)
            return _present(jobs_db.get_job(job_id))

        return api_router
