import boto3
from dotenv import load_dotenv
import os

load_dotenv('.env.local')


def initialize_db():
    ddb = boto3.resource('dynamodb',
                         endpoint_url=os.getenv('DYNAMODB_URL'),
                         region_name=os.getenv('DYNAMODB_REGION'),
                         aws_access_key_id=os.getenv('DYNAMODB_ACCESS_KEY'),
                         aws_secret_access_key=os.getenv('DYNAMODB_SECRET_KEY'))

    return ddb