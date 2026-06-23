"""SQS enqueue for combined-report jobs. The message is just the job_id; the
worker loads the full job (incl. the roster) from DynamoDB. Uses the Lambda
execution role for creds (SAM IAM policy)."""

import json
import os

import boto3


def _region():
    return os.getenv("AWS_REGION") or os.getenv("DYNAMODB_REGION") or "ap-south-1"


def enqueue_job(job_id: str) -> None:
    queue_url = os.getenv("REPORT_JOBS_QUEUE_URL")
    if not queue_url:
        raise RuntimeError("REPORT_JOBS_QUEUE_URL is not set")
    sqs = boto3.client("sqs", region_name=_region())
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps({"job_id": job_id}))
