from doctest import Example
from uuid import uuid4
from pydantic import Field
from decimal import Decimal
from pydantic import BaseModel
from pydantic.types import UUID4
from typing import List, Optional

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
    quiz_id: str = Field(..., example='QUIZ_ID')
    quiz_name: str = Field(..., example='Quiz Name')
    student_id: str = Field(..., example='STUDENT_ID')
    student_name: str = Field(..., example='Student Name')
    quiz_date: str = Field(..., example='2022-08-03')
    quiz_stats: QuizStats = Field()
    score_details: ScoreDetails = Field()


class StudentQuizReportModel(CreateStudentQuizReportModel):
    id: Optional[str] = Field(..., hidden=True)


class StudentQuizReportController():
    def __init__(self, student_quiz_reports_db: StudentQuizReportsDB) -> None:
        self.__student_quiz_reports_db = student_quiz_reports_db

    def get_all(self):
        return self.__student_quiz_reports_db.get_all()

    def get_student_quiz_report(self, student_id, quiz_id):
        student_id_quiz_id = student_id + "-" + quiz_id
        return self.__student_quiz_reports_db.get_student_quiz_report(student_id_quiz_id=student_id_quiz_id)

    def get_student_quiz_report(self, report_id):
        return self.__student_quiz_reports_db.get_student_quiz_report(report_id)

    def create_student_quiz_report(self, report_data: CreateStudentQuizReportModel, uid=None):
        uid = report_data.student_id + "-" + report_data.quiz_id
        
        uid = uid.replace(" ", "_")
        student_quiz_report = StudentQuizReportModel(**report_data.dict(), id=uid)
        return self.__student_quiz_reports_db.create_student_quiz_report(student_quiz_report.dict())

    def update_student_quiz_report(self, student_quiz_report: StudentQuizReportModel):
        return self.__student_quiz_reports_db.update_student_quiz_report(student_quiz_report.dict())

    def delete_student_quiz_report(self, uid: str):
        return self.__student_quiz_reports_db.delete_student_quiz_report(uid)
