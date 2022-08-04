from botocore.exceptions import ClientError
from boto3.resources.base import ServiceResource
from decimal import Decimal

import json

class StudentQuizReportsDB:
    def __init__(self, db: ServiceResource) -> None:
        self.__db = db

    def get_all(self):
        table = self.__db.Table('student_quiz_reports')
        response = table.scan()
        return response.get('Items', [])

    def get_student_quiz_report(self, student_id_quiz_id: str):
        try:
            print("Trying to find", student_id_quiz_id)
            table = self.__db.Table('student_quiz_reports')
            response = table.get_item(Key={'id': student_id_quiz_id})
            return response['Item']
        except ClientError as e:
            raise ValueError(e.response['Error']['Message'])

    def create_student_quiz_report(self, student_quiz_report: dict):
        table = self.__db.Table('student_quiz_reports')

        # Need to do this because otherwise dynamodb throws error about float not being supported
        # https://stackoverflow.com/questions/70343666/python-boto3-float-types-are-not-supported-use-decimal-types-instead
        student_quiz_report = json.loads(json.dumps(student_quiz_report), parse_float=Decimal)
        response = table.put_item(Item=student_quiz_report)
        return response
