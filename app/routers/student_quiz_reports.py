import os
from collections import OrderedDict
from typing import Optional, Union
from urllib.parse import unquote

import requests
from auth import verify_token
from db.reports_db import ReportsDB
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.templating import Jinja2Templates

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
    "weightage": "Weightage",
}

CHAPTER_WISE_ROW_NAMES = {
    "marks_scored": "Marks",
    "max_score": "Max Marks",
    "total_questions": "Number of Questions",
    "accuracy": "Accuracy",
    "chapter_name": "Chapter Name",
    "attempt_percentage": "Attempt Rate",
    "chapter_code": "Chapter Code",
}

QUIZ_URL = (
    "https://quiz.avantifellows.org/quiz/{quiz_id}?userId={user_id}&apiKey={api_key}"
)
# https://reports.avantifellows.org/reports/student_quiz_report/Homework_Quiz_2022-08-03_62ea813210de4e9677c8ce2d/1403899102
STUDENT_QUIZ_REPORT_URL = "https://reports.avantifellows.org/reports/student_quiz_report/{session_id}/{user_id}"

AF_API_KEY = "6qOO8UdF1EGxLgzwIbQN"

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


class StudentQuizReportsRouter:
    """
    Router class for handling Student Reports related endpoints.
    """

    def __init__(self, reports_db: ReportsDB) -> None:
        self.__reports_db = reports_db
        self._templates = Jinja2Templates(directory="templates")

    @property
    def router(self):
        api_router = APIRouter(prefix="/reports", tags=["reports"])

        def _parse_section_data(section=None):
            """
            Parse the section data and return a formatted section report.

            Args:
                section (dict): The section data.

            Returns:
                dict: The formatted section report.
            """
            section["name"] = section["user_id-section"].split("#")[1].capitalize()
            section_report = {}
            section_report["name"] = "Performance - " + section["name"].capitalize()
            table_data = {}

            # For main table
            for row in ROW_NAMES:
                if row in section:
                    table_data[ROW_NAMES[row]] = section[row]

            # For chapter level tables where the data exists.
            # Ignore if it doesn't exist like the "Overall section", but also
            # reports that don't have chapterwise data
            if "chapter_wise_data" in section:
                table_data["chapter_level_data"] = section["chapter_wise_data"]
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
            Returns all student reports for a given user ID.

            Args:
                request (Request): The request object.
                user_id (str): The user ID.
                format (str, optional): The format of the reports. Defaults to None.
                verified (bool): The verification status of the token.
                auth_header (str, optional): The API key header. Defaults to None.

            Raises:
                HTTPException: If the user is not verified or user ID is not specified.

            Returns:
                dict: The student reports.
            """
            if not verified:
                raise HTTPException(status_code=401, detail="Unauthorized")

            if user_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="User ID has to be specified",
                )
            elif format is not None and format == "json":
                data = self.__reports_db.get_student_reports(user_id)

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
                        "start_date": doc["start_date"],
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
            Returns a student quiz report for a given session ID and user ID.

            Args:
                request (Request): The request object.
                session_id (str): The session ID.
                user_id (str): The user ID.

            Raises:
                HTTPException: If session ID or user ID is not specified.

            Returns:
                TemplateResponse: The student quiz report template response.
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
            try:
                data = self.__reports_db.get_student_quiz_report(user_id, session_id)
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail="No student_quiz_report found. Unknown error occurred.",
                )

            if len(data) == 0:
                # no data
                error_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "error_message": "No report found. Please contact admin.",
                    "status_code": 404,
                }
                return self._templates.TemplateResponse(
                    "error.html", {"request": request, "error_data": error_data}
                )

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

        @api_router.get("/student_quiz_report/v2/{session_id}/{user_id}")
        def student_quiz_report_v2(
            request: Request,
            session_id: str,
            user_id: str,
            format: Union[str, None] = None,
        ):
            """
            Returns a student quiz report (V2) for a given session ID and user ID.

            Args:
                request (Request): The request object.
                session_id (str): The session ID.
                user_id (str): The user ID.

            Raises:
                HTTPException: If session ID or user ID is not specified.

            Returns:
                TemplateResponse: The student quiz report template response.
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
            try:
                data = self.__reports_db.get_student_quiz_report_v2(user_id, session_id)
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail="No student_quiz_report found. Unknown error occurred.",
                )

            if len(data) == 0:
                # no data
                error_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "error_message": "No report found. Please contact admin.",
                    "status_code": 404,
                }
                return self._templates.TemplateResponse(
                    "error.html", {"request": request, "error_data": error_data}
                )
            print(data[0])

            templateResponse = self._templates.TemplateResponse(
                "student_quiz_report_v2.html",
                {"request": request, "report_data": data[0]},
            )
            if format != "pdf":
                return templateResponse
            else:
                html_content = templateResponse.body
                html_content = html_content.decode("utf-8")  # Decode bytes to string

                # Convert bytes to string if necessary
                if isinstance(html_content, bytes):
                    html_content = html_content.decode()

                # Send HTML to PDF rendering service
                url = os.getenv("HTML_TO_PDF_SERVER_URL")
                response = requests.post(url, json={"html": html_content})
                # Check if the request was successful

                if response.status_code == 200:
                    # Return the PDF as a streaming response
                    return StreamingResponse(
                        response.iter_content(chunk_size=10240),
                        media_type="application/pdf",
                    )
                else:
                    return HTMLResponse(content="Error generating PDF", status_code=500)

        return api_router
