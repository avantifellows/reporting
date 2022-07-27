from student_quiz_reports import generate_student_quiz_reports, drop_student_quiz_reports
import boto3

def initialize_db():
    ddb = boto3.resource('dynamodb',
                         endpoint_url='http://localhost:8000',
                         region_name='ap-south-1',
                         aws_access_key_id='AKIARUBOPCTS7SQE7J54',
                         aws_secret_access_key='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')

    return ddb

def generate_tables():
    ddb = initialize_db()
    generate_student_quiz_reports(ddb)

def drop_tables():
    ddb = initialize_db()
    drop_student_quiz_reports(ddb)

if __name__ == '__main__':
    generate_tables()