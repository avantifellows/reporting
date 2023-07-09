from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, Depends
from collections import OrderedDict
from urllib.parse import unquote
from typing import Union, Optional
from auth import verify_token
from models.student_quiz_report import StudentQuizReportController
from fastapi.security.api_key import APIKeyHeader


ROW_NAMES = OrderedDict()
ROW_NAMES = {
    "marks_scored": "Marks",
    "num_skipped": "Unattempted",
    "num_wrong": "Wrong Answers",
    "num_correct": "Correct Answers",
    "num_partially_correct": "Partially Correct",
    "percentage": "Percentage",
    "accuracy": "Accuracy",
    "highest_test_score": "Topper Marks",
    "percentile": "Percentile",
    "rank": "Rank",
}

QUIZ_URL = (
    "https://quiz.avantifellows.org/quiz/{quiz_id}?userId={user_id}&apiKey={api_key}"
)
# https://reports.avantifellows.org/reports/student_quiz_report/Homework_Quiz_2022-08-03_62ea813210de4e9677c8ce2d/1403899102
STUDENT_QUIZ_REPORT_URL = "https://reports.avantifellows.org/reports/student_quiz_report/{session_id}/{user_id}"

AF_API_KEY = "6qOO8UdF1EGxLgzwIbQN"

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


class ReportsRouter:
    def __init__(
        self, student_quiz_reports_controller: StudentQuizReportController
    ) -> None:
        self.__student_quiz_reports_controller = student_quiz_reports_controller
        self._templates = Jinja2Templates(directory="templates")

    @property
    def router(self):
        api_router = APIRouter(prefix="/reports", tags=["reports"])

        def _parse_section_data(section=None):
            section["name"] = section["user_id-section"].split("#")[1].capitalize()
            section_report = {}
            section_report["name"] = "Performance - " + section["name"].capitalize()
            table_data = {}
            for row in ROW_NAMES:
                if row in section:
                    table_data[ROW_NAMES[row]] = section[row]

            section_report["table_data"] = table_data
            return section_report

        @api_router.get("/student_reports/{user_id}")
        def get_student_reports(
            request: Request,
            user_id: str = None,
            format: Union[str, None] = None,
            verified: bool = Depends(verify_token),
            auth_header: Optional[str] = Depends(api_key_header),
        ):
            """
            Returns all student reports for a given user ID
            params: user_id: str
            params: format: str
            params: verified: bool
            """
            if not verified:
                raise HTTPException(status_code=401, detail="Unauthorized")

            if user_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="User ID has to be specified",
                )
            elif format is not None and format == "json":
                data = self.__student_quiz_reports_controller.get_student_reports(
                    user_id=user_id
                )
                response = {"student_id": user_id}
                student_reports = []
                for doc in data:
                    if "overall" not in doc["user_id-section"]:
                        continue
                    result = {
                        "test_name": doc["test_name"],
                        "test_session_id": doc["session_id"],
                        "percentile": doc["percentile"] if "percentile" in doc else "",
                        "rank": doc["rank"] if "rank" in doc else "",
                        "report_link": STUDENT_QUIZ_REPORT_URL.format(
                            session_id=doc["session_id"], user_id=user_id
                        ),
                    }
                    student_reports.append(result)
                response["reports"] = student_reports
                return response
            else:
                return HTTPException(
                    status_code=501,
                    detail="Not implemented",
                )

        @api_router.get("/student_quiz_report/{session_id}/{user_id}")
        def student_quiz_report(request: Request, session_id: str, user_id: str):
            """
            Returns a student quiz report for a given session ID and user ID
            params: session_id: str
            params: user_id: str
            """
            if session_id is None or user_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Session ID and User ID have to be specified",
                )
            # decoding URL encoded values. As this information is coming through a URL,
            # it's possible that the strings are URL encoded.
            session_id = unquote(session_id)
            user_id = unquote(user_id)
            data = self.__student_quiz_reports_controller.get_student_quiz_report(
                    session_id=session_id, user_id=user_id
                )
            if isinstance(data, ValueError):
                raise HTTPException(status_code=400, detail="Invalid user_id or session_id")
            # try:
            #     data = self.__student_quiz_reports_controller.get_student_quiz_report(
            #         session_id=session_id, user_id=user_id
            #     )
            # except KeyError:
            #     raise HTTPException(
            #         status_code=400, detail="No student_quiz_report found"
            #     )
            report_data = {}
            report_data["student_name"] = ""
            test_id = data[0]["test_id"]
            user_id = data[0]["user_id"]

            report_data["student_id"] = user_id
            if "platform" in data[0] and data[0]["platform"] == "quizengine":
                report_data["test_link"] = QUIZ_URL.format(
                    quiz_id=test_id, user_id=user_id, api_key=AF_API_KEY
                )

            section_reports = []
            overall_performance = {}
            for section in data:
                parsed_section_data = _parse_section_data(section)
                if section["section"] == "overall":
                    overall_performance = parsed_section_data
                    report_data["percentage"] = parsed_section_data["table_data"][
                        "Percentage"
                    ]
                    report_data["test_name"] = section["test_name"]
                    report_data["test_date"] = section["start_date"]
                else:
                    section_reports.append(parsed_section_data)
            report_data["overall_performance"] = overall_performance
            report_data["section_reports"] = section_reports
            return self._templates.TemplateResponse(
                "student_quiz_report.html",
                {"request": request, "report_data": report_data},
            )

        return api_router
