from doctest import Example
from uuid import uuid4
from pydantic import Field
from decimal import Decimal
from pydantic import BaseModel
from pydantic.types import UUID4
from typing import List, Optional

from db.student_quiz_reports_db import StudentQuizReportsDB

class QuizStats(BaseModel):
    max_score: int = Field(..., example=100)
    average: float = Field(..., example=56.4)
    number_of_students: int = Field(..., example=72)
    highest_marks: float = Field(..., example=97.5)

class ScoreDetails(BaseModel):
    score: float = Field(..., example=65.5)
    rank: int = Field(..., example=7)
    percentile: float = Field(..., example=85.4)

class StudentQuizReportModel(BaseModel):
    id: Optional[str]
    quiz_id: str = Field(..., example='QUIZ_ID')
    quiz_name: str = Field(..., example='Quiz Name')
    student_id: str = Field(..., example='Student ID')
    student_name: str = Field(..., example='Student Name')
    quiz_stats: QuizStats = Field()
    score_details: ScoreDetails = Field()


class StudentQuizReportController():
    def __init__(self, repository: StudentQuizReportsDB) -> None:
        self.__repository = repository

    def get_all(self):
        return self.__repository.get_all()

    def get_student_quiz_report(self, student_id, quiz_id):
        student_id_quiz_id = student_id + "-" + quiz_id
        return self.__repository.get_student_quiz_report(student_id_quiz_id=student_id_quiz_id)

    def create_student_quiz_report(self, student_quiz_report: StudentQuizReportModel, uid=None):
        if (uid == None):
            uid = student_quiz_report.student_id + "-" + student_quiz_report.quiz_id
        student_quiz_report.student_id = student_quiz_report.student_id.replace(" ", "_")
        uid = uid.replace(" ", "_")
        student_quiz_report.id = uid
        return self.__repository.create_student_quiz_report(student_quiz_report.dict())

    def update_student_quiz_report(self, student_quiz_report: StudentQuizReportModel):
        return self.__repository.update_student_quiz_report(student_quiz_report.dict())

    def delete_student_quiz_report(self, uid: str):
        return self.__repository.delete_student_quiz_report(uid)