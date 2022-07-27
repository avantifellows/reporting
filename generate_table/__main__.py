from student_quiz_reports import generate_student_quiz_reports, drop_student_quiz_reports
import boto3

def initialize_db():
    ddb = boto3.resource('dynamodb',
                         endpoint_url='http://localhost:8000',
                         region_name='REGION',
                         aws_access_key_id='KEY',
                         aws_secret_access_key='SECRET_KEY')

    return ddb

def generate_tables():
    ddb = initialize_db()
    generate_student_quiz_reports(ddb)

def drop_tables():
    ddb = initialize_db()
    drop_student_quiz_reports(ddb)

if __name__ == '__main__':
    generate_tables()