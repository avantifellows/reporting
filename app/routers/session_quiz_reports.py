from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from db.sessions_db import SessionsDB
from db.quiz_db import QuizDB
from typing import Optional
from utils.pdf_converter import convert_template_to_pdf


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
        def get_live_session_report(
            request: Request,
            session_id: str = None,
            format: Optional[str] = None,
            debug: bool = False,
        ):
            """
            Returns live report for a given session ID (only quizzes supported for now)
            params:
                session_id: The session ID
                format: Optional format parameter. If "pdf", returns a PDF
                debug: If True and format is "pdf", returns the HTML that would be sent to PDF service
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

            template_response = self._templates.TemplateResponse(
                "live_session_report.html",
                {"request": request, "session_id": session_id, "data": data},
            )

            if format == "pdf":
                return convert_template_to_pdf(template_response, debug=debug)
            return template_response

        @api_router.get("/live_quiz_report/{quiz_id}")
        def get_live_quiz_report(
            request: Request,
            quiz_id: str = None,
            format: Optional[str] = None,
            debug: bool = False,
        ):
            """
            Returns live report for a given quiz ID
            params:
                quiz_id: The quiz ID
                format: Optional format parameter. If "pdf", returns a PDF
                debug: If True and format is "pdf", returns the HTML that would be sent to PDF service
            """
            if not quiz_id:
                raise HTTPException(status_code=400, detail="Quiz ID is required.")

            data = self.__quiz_db.get_live_quiz_stats(quiz_id=quiz_id)
            if not data:
                raise HTTPException(
                    status_code=400, detail="Quiz not found with provided Quiz ID."
                )

            template_response = self._templates.TemplateResponse(
                "live_session_report.html",
                {"request": request, "session_id": "", "data": data},
            )

            if format == "pdf":
                return convert_template_to_pdf(template_response, debug=debug)
            return template_response

        return api_router
