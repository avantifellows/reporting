from dotenv import load_dotenv
from google.cloud import firestore
import os
import json
import base64
import boto3
from google.cloud.firestore_v1.base_query import FieldFilter


def _load_firestore_encoded_key():
    """Return the base64-encoded Firestore service-account JSON.

    Prefer a raw FIRESTORE_CREDENTIALS env var (local dev / .env.local). In
    deployed Lambdas the creds live in Secrets Manager (named by
    FIRESTORE_CREDENTIALS_SECRET_NAME) instead of an env var — the full JSON is
    ~3KB and was pushing the function's env over Lambda's 4KB limit. Mirrors how
    BigQuery creds are loaded (BQ_CREDENTIALS_SECRET_NAME)."""
    if "FIRESTORE_CREDENTIALS" not in os.environ:
        load_dotenv("../../.env.local")
    encoded_key = os.getenv("FIRESTORE_CREDENTIALS")
    if encoded_key:
        return encoded_key
    secret_name = os.getenv("FIRESTORE_CREDENTIALS_SECRET_NAME")
    if secret_name:
        client = boto3.client("secretsmanager")
        return client.get_secret_value(SecretId=secret_name)["SecretString"]
    raise RuntimeError(
        "Firestore credentials not configured: set FIRESTORE_CREDENTIALS "
        "or FIRESTORE_CREDENTIALS_SECRET_NAME"
    )


class SessionsDB:
    """
    This class is used to interact with the Sessions Firestore collection
    As of 22/1/2024, the Sessions colletion is on Firestore till we migrate it to Postgres
    """

    def __init__(self) -> None:
        encoded_key = _load_firestore_encoded_key()
        SERVICE_ACCOUNT_JSON = json.loads(base64.b64decode(encoded_key).decode("utf-8"))
        self.__db = firestore.Client.from_service_account_info(SERVICE_ACCOUNT_JSON)

        self.__collection_name = "Sessions"

    def get_quiz_session(self, session_id):
        """
        Returns a quiz session for a given session ID.
        """
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

        return None
