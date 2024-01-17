from datetime import datetime
from datetime import timedelta
from bson import ObjectId
from pymongo import MongoClient


class QuizDB:
    def __init__(self, db: MongoClient) -> None:
        self.__db = db

    def __generate_objectid_for_time(self, time):
        timeId = str(ObjectId.from_datetime(time))
        return timeId

    def get_live_quiz_stats(self, quiz_id):
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        oid_7_days_ago = self.__generate_objectid_for_time(seven_days_ago)

        # Aggregation pipeline
        pipeline = [
            {
                # Match documents with the specified quizId
                "$match": {"quiz_id": quiz_id}
            },
            {
                # Match documents where _id is greater than the ObjectId 7 days ago
                "$match": {"_id": {"$gte": oid_7_days_ago}}
            },
            {
                # Group by user_id, quiz_id, and date to get unique sessions per user per day
                "$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "quiz_id": "$quiz_id",
                        "date": {
                            "year": {"$year": {"$toDate": {"$toObjectId": "$_id"}}},
                            "month": {"$month": {"$toDate": {"$toObjectId": "$_id"}}},
                            "day": {
                                "$dayOfMonth": {"$toDate": {"$toObjectId": "$_id"}}
                            },
                        },
                    },
                    "count": {"$sum": 1},
                }
            },
            {
                # Group by date to count unique sessions per day
                "$group": {"_id": "$_id.date", "uniqueSessions": {"$sum": 1}}
            },
            {
                # Sort the results by date
                "$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}
            },
            {
                # Format the output if needed
                "$project": {"_id": 0, "date": "$_id", "uniqueSessions": 1}
            },
        ]

        return list(self.__db.quiz.sessions.aggregate(pipeline))
