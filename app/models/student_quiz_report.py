from pydantic import Field
from pydantic import BaseModel
from typing import List


from db.student_quiz_reports_db import StudentQuizReportsDB


class CustomBaseModel(BaseModel):
    def dict(self, **kwargs):
        hidden_fields = set(
            attribute_name
            for attribute_name, model_field in self.__fields__.items()
            if model_field.field_info.extra.get("hidden") is True
        )
        kwargs.setdefault("exclude", hidden_fields)
        return super().dict(**kwargs)


class QuizStats(BaseModel):
    max_score: int = Field(..., example=100)
    average: float = Field(..., example=56.4)
    number_of_students: int = Field(..., example=72)
    highest_marks: float = Field(..., example=97.5)


class ScoreDetails(BaseModel):
    score: float = Field(..., example=65.5)
    rank: int = Field(..., example=7)
    percentile: float = Field(..., example=85.4)
    num_correct: int = Field(..., example=30)
    num_incorrect: int = Field(..., example=15)
    num_skipped: int = Field(..., example=7)
    max_marks: int = Field(..., example=360)
    highest_score: int = Field(..., example=325)


class CreateStudentQuizReportModel(BaseModel):
    id: str = Field(..., example="SESSION_ID_TEST_ID")
    session_id: str = Field(..., example="SESSION_ID")
    test_id: str = Field(..., example="TEST_ID")
    number_test_taker: int = Field(..., example="500")
    test_name: str = Field(..., example="Quiz Name")
    start_date: str = Field(..., example="2022-04-03")
    start_time: str = Field(..., example="8:00:00 PM")
    end_date: str = Field(..., example="2022-04-03")
    group: str = Field(..., example="GROUP")
    test_type: str = Field(..., example="TEST_TYPE")
    inserted_at_timestamp: str = Field(..., example="2022-08-09 14:08:00.618552")

    marks_scored: float = Field(..., example=25.4)
    num_wrong: int = Field(..., example=25)
    num_correct: int = Field(..., example=25)
    num_skipped: int = Field(..., example=5)
    highest_test_score: float = Field(..., example=50.3)
    percentile: float = Field(..., example=40.3)
    percentage: float = Field(..., example=20.2)

    max_marks_possible: int = Field(..., example=100)
    avg_test_score: float = Field(..., example=25.30)
    total_questions: float = Field(..., example=50)

    user_data_validated: bool = Field(..., example=True)

    section: str = Field(..., example="Chemistry")
    user_id: str = Field(..., example="USER_ID")
    student_name: str = Field(..., example="Student Name")
    start_date: str = Field(..., example="2022-08-03")


class StudentQuizReportModel(CreateStudentQuizReportModel):
    user_id_section: str = Field(..., example="", alias="user_id-section")


class StudentQuizReportController:
    def __init__(self, student_quiz_reports_db: StudentQuizReportsDB) -> None:
        self.__student_quiz_reports_db = student_quiz_reports_db

    def get_all(self):
        return self.__student_quiz_reports_db.get_all()

    def get_student_quiz_report(self, user_id, session_id):
        return self.__student_quiz_reports_db.get_student_quiz_report(
            user_id, session_id
        )

    def create_student_quiz_report(self, report_data: CreateStudentQuizReportModel):
        uid = report_data.student_id + "-" + report_data.quiz_id

        uid = uid.replace(" ", "_")
        student_quiz_report = StudentQuizReportModel(**report_data.dict(), id=uid)
        return self.__student_quiz_reports_db.create_student_quiz_report(
            student_quiz_report.dict()
        )

    def get_student_quiz_report_by_session_id(self, session_id: str) -> List[dict]:
        try:
            report_data = self.__student_quiz_reports_db.get_student_quiz_report(
                session_id=session_id, user_id=""
            )
        except KeyError:
            raise ValueError("No student_quiz_report found")
        return report_data
