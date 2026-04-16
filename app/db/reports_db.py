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
                & Key("user_id-section").begins_with(f"{user_id}#")
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
        except ClientError:
            return []

    def get_student_reports_v2(self, user_id):
        """
        Returns all student reports from the v2 table for a given user ID.
        Uses the user_id_index GSI.
        """
        try:
            table = self.__db.Table("student_quiz_reports_v2")
            response = table.query(
                IndexName="user_id_index",
                KeyConditionExpression=Key("user_id").eq(user_id),
            )
            return response["Items"]
        except ClientError:
            return []

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
        Returns a student quiz report from the v2 table by querying the
        session_id partition and filtering for matching student_id or apaar_id.
        Empty apaar_id values are excluded from the apaar_id match since many
        records have apaar_id="".
        params:
            identifier: The student_id or apaar_id to match (must be non-empty)
            session_id: The session ID
        Returns:
            The report item if found, None otherwise.
        """
        if not identifier:
            return None
        try:
            table = self.__db.Table("student_quiz_reports_v2")
            kwargs = dict(
                KeyConditionExpression=Key("session_id").eq(session_id),
                FilterExpression=(
                    "student_id = :id OR (apaar_id = :id AND apaar_id <> :empty)"
                ),
                ExpressionAttributeValues={":id": identifier, ":empty": ""},
            )
            while True:
                response = table.query(**kwargs)
                items = response.get("Items", [])
                if items:
                    return items[0]
                lek = response.get("LastEvaluatedKey")
                if not lek:
                    return None
                kwargs["ExclusiveStartKey"] = lek
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])
