from app.db.reports_db import ReportsDB


class QuizReports:
    def __init__(self, reports_db: ReportsDB) -> None:
        self.__reports_db = reports_db

    def live_quiz_stats(self):
        # Implementation of live_quiz_stats method
        pass
