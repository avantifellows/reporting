from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient


class QuizDB:
    def __init__(self, db: MongoClient) -> None:
        self.__db = db

    def __generate_objectid_for_time(self, time):
        timeId = str(ObjectId.from_datetime(time))
        return timeId

    def get_live_quiz_stats(self, quiz_id, start_date=None, end_date=None):
        """
        Returns daywise report for a given quiz ID
        params:
            quiz_id: The quiz ID
            start_date (optional): The start date for the report
            end_date (optional): The end date for the report
        """

        # Get quiz details
        quiz = self.__db.quiz.quizzes.find_one({"_id": quiz_id})
        quiz_title = quiz.get("title", "") if quiz else ""

        pipeline = []
        pipeline.append({"$match": {"quiz_id": quiz_id}})

        if start_date is not None:
            start_datetime = datetime.strptime(
                start_date + ":00:00:00", "%Y-%m-%d:%H:%M:%S"
            )
            oid_start = self.__generate_objectid_for_time(start_datetime)
            pipeline.append({"$match": {"_id": {"$gte": oid_start}}})

        if end_date is not None:
            end_datetime = datetime.strptime(
                end_date + ":23:59:59", "%Y-%m-%d:%H:%M:%S"
            )
            oid_end = self.__generate_objectid_for_time(end_datetime)
            pipeline.append({"$match": {"_id": {"$lte": oid_end}}})
        else:
            end_datetime = datetime.now()

        # Aggregation pipeline
        pipeline.extend(
            [
                {
                    # Group by user_id, quiz_id, and date to get unique sessions per user per day
                    "$group": {
                        "_id": {
                            "user_id": "$user_id",
                            "quiz_id": "$quiz_id",
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": {"$toDate": {"$toObjectId": "$_id"}},
                                }
                            },
                        },
                        "count": {"$sum": 1},
                    }
                },
                {
                    # Group by date to count unique sessions per day
                    "$group": {
                        "_id": "$_id.date",
                        "uniqueSessions": {"$sum": 1},
                    }
                },
                {
                    # Sort the results by date
                    "$sort": {"_id.date": 1}
                },
                {
                    # Format the output if needed
                    "$project": {"_id": 0, "date": "$_id", "uniqueSessions": 1}
                },
            ]
        )

        # Get the total sessions
        pipeline.append(
            {
                "$group": {
                    "_id": None,
                    "totalSessions": {"$sum": "$uniqueSessions"},
                    "data": {"$push": "$$ROOT"},
                }
            }
        )

        # Reshape the final output
        pipeline.append(
            {
                "$project": {
                    "_id": 0,
                    "totalSessions": 1,
                    "quizTitle": 1,
                    "daywise_results": "$data",
                }
            }
        )

        # Run the pipeline
        daywise_results = list(self.__db.quiz.sessions.aggregate(pipeline))
        print(daywise_results)

        # Format the final output including the quiz title
        final_result = {
            "quizTitle": quiz_title,
            "totalSessions": daywise_results[0]["totalSessions"],
            "daywiseStats": daywise_results[0]["daywise_results"],
        }
        return final_result