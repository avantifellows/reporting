import boto3
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import json
from google.oauth2 import service_account
from google.cloud import bigquery

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
        "BQ_CREDENTIALS_SECRET_NAME",
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


def initialize_bigquery():
    secret_name = os.environ.get("BQ_CREDENTIALS_SECRET_NAME")
    client = boto3.client(
        "secretsmanager", region_name="ap-south-1"
    )  # no need for credentials - lambda will provide
    secret_value = client.get_secret_value(SecretId=secret_name)
    credentials_json = json.loads(secret_value["SecretString"])
    credentials = service_account.Credentials.from_service_account_info(
        credentials_json
    )

    bigquery_details = {
        "project": "avantifellows",
        "region": "asia-south1",
    }

    return bigquery.Client(
        project=bigquery_details["project"],
        location=bigquery_details["region"],
        credentials=credentials,
    )
