import boto3
from dotenv import load_dotenv
import os

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
    ]
):
    load_dotenv("../.env.local")


def initialize_db():
    ddb = boto3.resource(
        "dynamodb",
        endpoint_url=os.getenv("DYNAMODB_URL"),
        region_name=os.getenv("DYNAMODB_REGION"),
        aws_access_key_id=os.getenv("DYNAMODB_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("DYNAMODB_SECRET_KEY"),
    )

    return ddb
