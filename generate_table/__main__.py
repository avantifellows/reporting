from student_quiz_reports import (
    generate_student_quiz_reports,
    drop_student_quiz_reports,
)
import boto3
from dotenv import load_dotenv

import os

# Update and use `.env.prod` to write to prod dynamodb table
# or use `.env.staging` to write to staging dynamodb table
# TODO: Staging table doesn't exist as of now :p - so maybe we should create it in the future
load_dotenv(".env.local")


def initialize_db():
    ddb = boto3.resource(
        "dynamodb",
        endpoint_url=os.environ.get("DYNAMODB_URL"),
        region_name=os.environ.get("DYNAMODB_REGION"),
        aws_access_key_id=os.environ.get("DYNAMODB_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("DYNAMODB_SECRET_KEY"),
    )

    return ddb


def generate_tables():
    ddb = initialize_db()
    generate_student_quiz_reports(ddb)


def drop_tables():
    ddb = initialize_db()
    drop_student_quiz_reports(ddb)


if __name__ == "__main__":
    generate_tables()
