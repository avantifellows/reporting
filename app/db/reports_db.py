from botocore.exceptions import ClientError
from boto3.resources.base import ServiceResource
from decimal import Decimal
from boto3.dynamodb.conditions import Key


import json


class ReportsDB:
    def __init__(self, db: ServiceResource) -> None:
        self.__db = db

    def get_all(self):
        table = self.__db.Table("student_quiz_reports")
        response = table.scan()
        return response.get("Items", [])

    def get_student_quiz_report(self, user_id, session_id):
        try:
            table = self.__db.Table("student_quiz_reports")
            response = table.query(
                KeyConditionExpression=Key("session_id").eq(session_id)
                & Key("user_id-section").begins_with(user_id)
            )
            return response["Items"]
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])

    def get_quiz_report_data(self, quiz_id):
        try:
            table = self.__db.Table("student_quiz_reports")
            response = table.query(KeyConditionExpression=Key("session_id").eq(quiz_id))
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])
        return response

    def create_student_quiz_report(self, student_quiz_report: dict):
        table = self.__db.Table("student_quiz_reports")

        # Need to do this because otherwise dynamodb throws error about float not being supported
        # https://stackoverflow.com/questions/70343666/python-boto3-float-types-are-not-supported-use-decimal-types-instead
        student_quiz_report = json.loads(
            json.dumps(student_quiz_report), parse_float=Decimal
        )
        response = table.put_item(Item=student_quiz_report)
        return response
