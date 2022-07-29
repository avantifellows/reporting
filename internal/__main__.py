from student_quiz_reports import generate_student_quiz_reports, drop_student_quiz_reports
import boto3
from dotenv import load_dotenv

import os

load_dotenv('.env.local')
def initialize_db():
    print("INITIALIZING DB")
    print(os.environ.get('DYNAMODB_REGION'))
    ddb = boto3.resource('dynamodb',
                         endpoint_url=os.environ.get('DYNAMODB_URL'),
                         region_name=os.environ.get('DYNAMODB_REGION'),
                         aws_access_key_id=os.environ.get('DYNAMODB_ACCESS_KEY'),
                         aws_secret_access_key=os.environ.get('DYNAMODB_SECRET_KEY'))

    return ddb
def generate_tables():
    ddb = initialize_db()
    generate_student_quiz_reports(ddb)

def drop_tables():
    ddb = initialize_db()
    drop_student_quiz_reports(ddb)

if __name__ == '__main__':
    generate_tables()