import io
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from db.sessions_db import SessionsDB
from db.quiz_db import QuizDB


class SessionQuizReportsRouter:
    """
    Router class for handling Session and Quiz Reports related endpoints.
    """

    def __init__(self, quiz_db: QuizDB, sessions_db: SessionsDB) -> None:
        self.__quiz_db = quiz_db
        self.__sessions_db = sessions_db
        self._templates = Jinja2Templates(directory="templates")

    @property
    def router(self):
        api_router = APIRouter(prefix="/reports", tags=["reports"])
        self._templates = Jinja2Templates(directory="templates")

        @api_router.get("/live_session_report/{session_id}")
        def get_live_session_report(request: Request, session_id: str = None):
            """
            Returns live report for a given session ID (only quizzes supported for now)
            params:
                session_id: The session ID
            """
            if not session_id:
                raise HTTPException(status_code=400, detail="Session ID is required.")

            session_data = self.__sessions_db.get_quiz_session(session_id=session_id)
            if session_data is None:
                raise HTTPException(status_code=404, detail="Session ID not found.")
            quiz_id = session_data["redirectPlatformParams"]["id"]
            start_date = session_data["startDate"]
            end_date = session_data["endDate"]
            data = self.__quiz_db.get_live_quiz_stats(
                quiz_id=quiz_id, start_date=start_date, end_date=end_date
            )
            return self._templates.TemplateResponse(
                "live_session_report.html",
                {"request": request, "session_id": session_id, "data": data},
            )

        @api_router.get("/live_quiz_report/{quiz_id}")
        def get_live_quiz_report(request: Request, quiz_id: str = None):
            """
            Returns live report for a given quiz ID
            params:
                quiz_id: The quiz ID
            """
            if not quiz_id:
                raise HTTPException(status_code=400, detail="Quiz ID is required.")

            data = self.__quiz_db.get_live_quiz_stats(quiz_id=quiz_id)
            if not data:
                raise HTTPException(
                    status_code=400, detail="Quiz not found with provided Quiz ID."
                )
            return self._templates.TemplateResponse(
                "live_session_report.html",
                {"request": request, "session_id": "", "data": data},
            )

        @api_router.get("/session_report/{session_id}")
        def get_session_report(
            request: Request,
            session_id: str,
            format: Optional[str] = None,
            sort_by: Optional[str] = None,
        ):
            """
            Returns list of all the students for a given Session ID
            params:
                session_id: The session ID
            """
            students = self.__reports_db.get_all_students_by_session(session_id)

            # Formatting students for response
            formatted_students = [
                {
                    "user_id": item["user_id-section"].split("#")[0],
                    "marks_scored": item.get("marks_scored", 0),
                    "percentage": item.get("percentage", 0),
                    "rank": item.get("rank", None),
                }
                for item in students
                if "user_id-section" in item and "overall" in item["user_id-section"]
            ]

            if sort_by == "highest_score":
                formatted_students.sort(
                    key=lambda x: (
                        -x["marks_scored"]
                        if x["marks_scored"] is not None
                        else float("-inf")
                    )
                )
            if format == "json":
                return {"session_id": session_id, "students": formatted_students}
            elif format == "excel":
                # Create DataFrame for Excel export
                df = pd.DataFrame(formatted_students)
                # Rename columns for better readability
                df = df.rename(
                    columns={
                        "user_id": "Student ID",
                        "marks_scored": "Marks",
                        "percentage": "Percentage",
                        "rank": "Rank",
                    }
                )

                # Create Excel file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Student Reports")
                output.seek(0)

                # Return Excel file as response
                headers = {
                    "Content-Disposition": f'attachment; filename="session_{session_id}_report.xlsx"'
                }
                return StreamingResponse(
                    output,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers=headers,
                )

            return self._templates.TemplateResponse(
                "session_report.html",
                {
                    "request": request,
                    "session_id": session_id,
                    "students": formatted_students,
                },
            )

        return api_router
