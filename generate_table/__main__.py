from student_quiz_reports import (
    generate_student_quiz_reports,
    drop_student_quiz_reports,
    add_secondary_index,
    drop_secondary_index,
)
from dotenv import load_dotenv
import boto3
import os

# Update and use `.env.prod` to write to prod dynamodb table
# or use `.env.staging` to write to staging dynamodb table
# TODO: Staging table doesn't exist as of now :p - so maybe we should create it in the future
load_dotenv(".env.local")

print("HELLO")
print(os.environ.get("DYNAMODB_URL"))
print(os.environ.get("DYNAMODB_ACCESS_KEY"))


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


def add_secondary_ind():
    # DON'T RUN THIS for the key user_id key as it's already been run
    ddb = initialize_db()
    add_secondary_index(ddb)


def drop_secondary_ind():
    drop_secondary_index("gsi_user_id-section")


if __name__ == "__main__":
    add_secondary_ind()
