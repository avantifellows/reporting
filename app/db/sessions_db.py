from dotenv import load_dotenv
from google.cloud import firestore
import os
import json
import base64
from google.cloud.firestore_v1.base_query import FieldFilter


class SessionsDB:
    def __init__(self) -> None:
        # Import the environment variables (not needed for prod as it will be in GH secrets)
        if "FIRESTORE_CREDENTIALS" not in os.environ:
            load_dotenv("../../.env.local")
        encoded_key = os.getenv("FIRESTORE_CREDENTIALS")
        SERVICE_ACCOUNT_JSON = json.loads(base64.b64decode(encoded_key).decode("utf-8"))
        self.__db = firestore.Client.from_service_account_info(SERVICE_ACCOUNT_JSON)

        self.__collection_name = "Sessions"

    def get_quiz_session(self, session_id):
        # Create a query against the collection
        sessions_ref = self.__db.collection(self.__collection_name)
        query = sessions_ref.where(
            filter=FieldFilter("redirectPlatform", "==", "quiz")
        ).where(filter=FieldFilter("id", "==", session_id))

        # Execute the query and print the results
        docs = query.stream()

        # Iterate over docs and return the first one (since we are assuming there is only one session per session ID)
        for doc in docs:
            return doc.to_dict()

        # Return None if no documents are found
        return None
