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
    """
    Generates all required dynamodb table (for now only student_quiz_reports)
    """
    ddb = initialize_db()
    generate_student_quiz_reports(ddb)


def drop_tables():
    """
    Empty the database of all the tables
    """
    ddb = initialize_db()
    drop_student_quiz_reports(ddb)


def add_secondary_ind():
    ddb = initialize_db()
    add_secondary_index(ddb)


def drop_secondary_ind(index_name: str):
    """
    Drops a secondary index
    """
    ddb = initialize_db()
    drop_secondary_index(ddb, index_name)


if __name__ == "__main__":
    """
    Creates empty dynamodb table with correct schema for local usage.
    """
    generate_tables()
    add_secondary_ind()
