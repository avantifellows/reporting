"""S3 helpers for combined-report PDFs.

Uses the Lambda execution role for credentials (IAM policy granted in the SAM
template) rather than the explicit keys DynamoDB uses, since the bucket lives in
the same account as the function.
"""

import os

import boto3
from botocore.config import Config


def _region():
    return os.getenv("AWS_REGION") or os.getenv("DYNAMODB_REGION") or "ap-south-1"


def _client():
    # Force the regional, virtual-hosted endpoint + SigV4. Without this the
    # presigned URL can target the global endpoint, which 307-redirects to the
    # regional host; following that redirect changes the signed Host header and
    # S3 rejects it with SignatureDoesNotMatch.
    return boto3.client(
        "s3",
        region_name=_region(),
        config=Config(
            signature_version="s3v4", s3={"addressing_style": "virtual"}
        ),
    )


def _bucket():
    bucket = os.getenv("REPORTS_S3_BUCKET")
    if not bucket:
        raise RuntimeError("REPORTS_S3_BUCKET is not set")
    return bucket


def build_key(session_id, school_code, job_id):
    """combined-reports/{session_id}/{school_code}/{job_id}.pdf — job_id keys the
    object so two sessions sharing a test name never collide."""
    return f"combined-reports/{session_id}/{school_code}/{job_id}.pdf"


def upload_pdf(key, pdf_bytes):
    _client().put_object(
        Bucket=_bucket(),
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )
    return key


def presigned_url(key, expires_in=3600):
    """Fresh presigned GET URL — generated on each status poll, never stored."""
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket(), "Key": key},
        ExpiresIn=expires_in,
    )
