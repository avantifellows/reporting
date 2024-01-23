import boto3
from dotenv import load_dotenv
import os
from pymongo import MongoClient

# when running app locally -- use load_dotenv
# when running app via gh actions -- variables already exist via secrets
# so no need to load_dotenv
if not all(
    key in os.environ
    for key in [
        "DYNAMODB_URL",
        "DYNAMODB_REGION",
        "DYNAMODB_ACCESS_KEY",
        "DYNAMODB_SECRET_KEY",
        "MONGO_AUTH_CREDENTIALS",
    ]
):
    # Update and use `.env.prod` to access the prod dynamodb table
    # or use `.env.staging` to access the staging dynamodb table
    # TODO: Staging table doesn't exist as of now :p - so maybe we should create it in the future
    load_dotenv("../.env.local")


def initialize_reports_db():
    ddb = boto3.resource(
        "dynamodb",
        endpoint_url=os.getenv("DYNAMODB_URL"),
        region_name=os.getenv("DYNAMODB_REGION"),
        aws_access_key_id=os.getenv("DYNAMODB_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("DYNAMODB_SECRET_KEY"),
    )

    return ddb


def initialize_quiz_db():
    quiz_db = MongoClient(os.getenv("MONGO_AUTH_CREDENTIALS"))
    return quiz_db
