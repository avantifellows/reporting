from botocore.exceptions import ClientError
from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key


class ReportsDB:
    """
    This class is used to interact with the Reports DynamoDB table
    """

    def __init__(self, db: ServiceResource) -> None:
        self.__db = db

    def get_all(self):
        table = self.__db.Table("student_quiz_reports")
        response = table.scan()
        return response.get("Items", [])

    def get_student_quiz_report(self, user_id, session_id):
        """
        Returns a student quiz report for a given session ID and user ID.
        params:
            user_id: The user ID
            session_id: The session ID
        """
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
        """
        Returns all student reports for a given user ID.
        params:
            user_id: The user ID
        """
        try:
            table = self.__db.Table("student_quiz_reports")
            response = table.query(
                IndexName="gsi_user_id",
                KeyConditionExpression=Key("user_id").eq(user_id),
            )
            return response["Items"]
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])
