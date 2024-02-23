from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient


class QuizDB:
    """
    Class to handle all the database operations related to quizzes (currently stored on Mongo Atlas)
    """

    def __init__(self, db: MongoClient) -> None:
        self.__db = db

    def __generate_objectid_for_time(self, time):
        """
        Generates a Mongo object ID for a given time
        """
        timeId = str(ObjectId.from_datetime(time))
        return timeId

    def get_live_quiz_stats(self, quiz_id, start_date=None, end_date=None):
        """
        Returns daywise report for a given quiz ID by using an aggregation pipeline

        params:
            quiz_id: The quiz ID
            start_date (optional): The start date for the report
            end_date (optional): The end date for the report
        """

        # Get quiz details
        quiz = self.__db.quiz.quizzes.find_one({"_id": quiz_id})
        if quiz is None:
            return None

        quiz_title = quiz.get("title", "") if quiz else ""
        pipeline = []
        # Narrow down documents by quiz ID
        pipeline.append({"$match": {"quiz_id": quiz_id}})

        # Narrow down documents by start and end date
        # (if start and end dates are not specified (for live quiz report), then no filters are applied)
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
        else:
            end_datetime = datetime.now()
        oid_end = self.__generate_objectid_for_time(end_datetime)

        # Get documents only matching quiz ID
        pipeline.append({"$match": {"_id": {"$lte": oid_end}}})

        # Group by user_id,and date to get unique sessions per user per day
        # Note that we don't need to group by quiz because the documents already
        # are matched to this quiz.
        # Also include data of how many of these users finished the quiz
        pipeline.extend(
            [
                {
                    "$group": {
                        "_id": {
                            "user_id": "$user_id",
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": {"$toDate": {"$toObjectId": "$_id"}},
                                }
                            },
                        },
                        "hasQuizEnded": {"$max": "$has_quiz_ended"},
                    }
                }
            ]
        )

        # Group by date again to count how many users attempted/finished the quiz each day
        pipeline.extend(
            [
                {
                    "$group": {
                        "_id": "$_id.date",
                        "totalUniqueUsers": {"$addToSet": "$_id.user_id"},
                        "uniqueSessions": {"$sum": 1},
                        "finishedSessions": {
                            "$sum": {"$cond": [{"$eq": ["$hasQuizEnded", True]}, 1, 0]}
                        },
                    }
                }
            ]
        )

        # Sort by date and format.
        # TODO: Projecting may not be necessary at this stage. But it doesn't affect
        # efficiency and makes the following steps cleaner
        pipeline.extend(
            [
                {"$sort": {"_id": -1}},
                {
                    "$project": {
                        "_id": 0,
                        "totalUniqueUsers": 1,
                        "date": "$_id",
                        "uniqueSessions": 1,
                        "finishedSessions": 1,
                    }
                },
            ]
        )

        # After this stage totalUniqueUsers will be an array of arrays
        # each array containing the user_ids for that particular day
        pipeline.append(
            {
                "$group": {
                    "_id": None,
                    "totalUniqueUsers": {"$push": "$_id.user_id"},
                    "totalFinishedSessions": {"$sum": "$finishedSessions"},
                    "data": {"$push": "$$ROOT"},
                }
            }
        )

        # Reshape the final output to get a nice dictionary
        # To find the totalUniqueUsersCount --
        # 1. Concatenate arrays to get array of arrays
        # 2. Reduce to make it a big array
        # 3. Use setUnion to get only unique values
        pipeline.append(
            {
                "$project": {
                    "_id": 0,
                    "totalFinishedSessions": 1,
                    "quizTitle": 1,
                    "daywise_results": "$data",
                    "totalSessions": {
                        "$size": {
                            "$setUnion": {
                                "$reduce": {
                                    "input": "$data.totalUniqueUsers",
                                    "initialValue": [],
                                    "in": {"$concatArrays": ["$$value", "$$this"]},
                                }
                            }
                        }
                    },
                }
            }
        )

        # Run the pipeline
        daywise_results = list(self.__db.quiz.sessions.aggregate(pipeline))
        if len(daywise_results) > 0:
            daywise_results = daywise_results[0]
        else:
            daywise_results = {
                "totalSessions": 0,
                "totalFinishedSessions": 0,
                "daywise_results": [],
            }

        # Format the final output including the quiz title
        final_result = {
            "quizTitle": quiz_title,
            "totalSessions": daywise_results["totalSessions"],
            "totalFinishedSessions": daywise_results["totalFinishedSessions"],
            "daywiseStats": daywise_results["daywise_results"],
        }
        return final_result
