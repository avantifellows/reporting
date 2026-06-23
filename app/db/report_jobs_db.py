import os
import uuid
from datetime import datetime, timezone

from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Job status lifecycle (see docs/combined-reports-contract.md)
QUEUED = "queued"
STARTED = "started"
PROCESSING = "processing"
DONE = "done"
ERRORED = "errored"


class ReportJobsDB:
    """
    Interacts with the `report_jobs` DynamoDB table that tracks combined-report
    generation jobs (status lifecycle, S3 output key, the school roster the
    worker filters against). One row per job, keyed by job_id; a GSI on
    session_school lets af_lms list a school's jobs for a test.
    """

    def __init__(self, db: ServiceResource) -> None:
        self.__db = db
        self.__table_name = os.getenv("REPORT_JOBS_TABLE_NAME", "report_jobs")

    def _table(self):
        return self.__db.Table(self.__table_name)

    def create_job(
        self,
        *,
        session_id: str,
        school: dict,
        students: list,
        test_name: str = None,
        requested_by: str = None,
    ) -> dict:
        """Write a new job in `queued` status and return the record."""
        job_id = str(uuid.uuid4())
        now = _now_iso()
        school_code = school.get("code") or school.get("udise") or "unknown"
        item = {
            "job_id": job_id,
            "session_school": f"{session_id}#{school_code}",
            "session_id": session_id,
            "school_code": school_code,
            "school_udise": school.get("udise"),
            "school_name": school.get("name"),
            "test_name": test_name,
            "status": QUEUED,
            "students": students,
            "student_count": len(students),
            "matched_count": None,
            "missing_count": None,
            "requested_by": requested_by,
            "error": None,
            "s3_key": None,
            "retry_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        try:
            self._table().put_item(Item=item)
            return item
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])

    def get_job(self, job_id: str):
        try:
            response = self._table().get_item(Key={"job_id": job_id})
            return response.get("Item")
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])

    def list_jobs(self, session_id: str, school_code: str) -> list:
        """Most-recent-first jobs for a (session, school) pair, via the GSI."""
        try:
            response = self._table().query(
                IndexName="session_school_index",
                KeyConditionExpression=Key("session_school").eq(
                    f"{session_id}#{school_code}"
                ),
                ScanIndexForward=False,
            )
            return response.get("Items", [])
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])

    def update(self, job_id: str, **fields) -> None:
        """Patch arbitrary attributes on a job, always bumping updated_at."""
        fields["updated_at"] = _now_iso()
        # `status` is a DynamoDB reserved word -> alias every name to be safe.
        names = {f"#{k}": k for k in fields}
        values = {f":{k}": v for k, v in fields.items()}
        set_expr = ", ".join(f"#{k} = :{k}" for k in fields)
        try:
            self._table().update_item(
                Key={"job_id": job_id},
                UpdateExpression=f"SET {set_expr}",
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
            )
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])

    def bump_retry(self, job_id: str, current_retry: int) -> None:
        self.update(
            job_id,
            status=QUEUED,
            retry_count=(current_retry or 0) + 1,
            error=None,
            s3_key=None,
        )
