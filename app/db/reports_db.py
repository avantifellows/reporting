from botocore.exceptions import ClientError
from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key


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

    def get_student_reports(self, user_id):
        try:
            table = self.__db.Table("student_quiz_reports")
            response = table.query(
                IndexName="gsi_user_id",
                KeyConditionExpression=Key("user_id").eq(user_id),
            )
            return response["Items"]
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])
