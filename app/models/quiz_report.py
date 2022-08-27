from db.reports_db import ReportsDB


class QuizReportController:
    def __init__(self, quiz_reports_db: ReportsDB) -> None:
        self.__quiz_reports_db = quiz_reports_db

    def get_quiz_report(self, quiz_id):
        data = self.__quiz_reports_db.get_quiz_report_data(quiz_id)
        if data is None or len(data) == 0:
            return None
        return data
