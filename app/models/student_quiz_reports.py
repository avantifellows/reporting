from pydantic import Field
from pydantic import BaseModel

# NOTE: THESE models are not used in the code, but keeping them here to inform the dynamoDB schema till we find a better way to do it.


class QuizStats(BaseModel):
    max_score: int = Field(..., example=100)
    average: float = Field(..., example=56.4)
    number_of_students: int = Field(..., example=72)
    highest_marks: float = Field(..., example=97.5)


class StudentQuizReportModel(BaseModel):
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
    num_partially_correct: int = Field(..., example=10)
    num_skipped: int = Field(..., example=5)
    highest_test_score: float = Field(..., example=50.3)
    percentile: float = Field(..., example=40.3)
    percentage: float = Field(..., example=20.2)
    accuracy: float = Field(..., example=30.5)

    max_marks_possible: int = Field(..., example=100)
    avg_test_score: float = Field(..., example=25.30)
    total_questions: float = Field(..., example=50)

    user_data_validated: bool = Field(..., example=True)

    section: str = Field(..., example="Chemistry")
    user_id: str = Field(..., example="USER_ID")
    student_name: str = Field(..., example="Student Name")
    start_date: str = Field(..., example="2022-08-03")
    user_id_section: str = Field(..., example="", alias="user_id-section")
