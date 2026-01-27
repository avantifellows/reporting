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

    def get_student_quiz_report_v2(self, user_id, session_id):
        """
        Returns a student quiz report from the v2 table for a given session ID and user ID.
        params:
            user_id: The user ID
            session_id: The session ID
        Returns:
            The report item if found, None otherwise.
        """
        try:
            table = self.__db.Table("student_quiz_reports_v2")
            response = table.get_item(
                Key={"session_id": session_id, "user_id": user_id}
            )
            return response.get("Item")
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])

    def get_student_quiz_report_v2_by_alt_id(self, identifier, session_id):
        """
        Returns a student quiz report from the v2 table by scanning with filters
        for session_id and matching student_id or apaar_id.
        params:
            identifier: The student_id or apaar_id to match
            session_id: The session ID
        Returns:
            The report item if found, None otherwise.
        """
        try:
            table = self.__db.Table("student_quiz_reports_v2")
            response = table.scan(
                FilterExpression="session_id = :sid AND (student_id = :id OR apaar_id = :id)",
                ExpressionAttributeValues={
                    ":sid": session_id,
                    ":id": identifier,
                },
            )
            items = response.get("Items", [])
            return items[0] if items else None
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])
