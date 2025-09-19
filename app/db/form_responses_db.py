from botocore.exceptions import ClientError
from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key
import os


class FormResponsesDB:
    """
    This class is used to interact with the Form Responses DynamoDB table
    """

    def __init__(self, db: ServiceResource) -> None:
        self.__db = db

    def get_form_responses(self, session_id, user_id):
        """
        Returns form responses for a given session ID and user ID.
        params:
            session_id: The session ID
            user_id: The user ID
        """
        try:
            table_name = os.environ.get(
                "DYNAMODB_FORM_RESPONSES_TABLE_NAME", "form_question_responses"
            )
            table = self.__db.Table(table_name)

            # Query by session_id and filter by user_id
            user_responses = table.query(
                KeyConditionExpression=Key("session_id").eq(session_id)
                & Key("user_id-question_position_index").begins_with(f"{user_id}#")
            )["Items"]

            # Sort by question_position_index to maintain order
            user_responses.sort(key=lambda x: int(x.get("question_position_index", 0)))

            return user_responses
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])

    def get_all_form_responses(self, session_id):
        """
        Returns all form responses for a given session ID.
        params:
            session_id: The session ID
        """
        try:
            table_name = os.environ.get(
                "DYNAMODB_FORM_RESPONSES_TABLE_NAME", "form_question_responses"
            )
            table = self.__db.Table(table_name)
            response = table.query(
                KeyConditionExpression=Key("session_id").eq(session_id)
            )
            return response.get("Items", [])
        except ClientError as e:
            raise ValueError(e.response["Error"]["Message"])
