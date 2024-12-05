from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from db.sessions_db import SessionsDB
from db.quiz_db import QuizDB
from jinja2 import TemplateError
import logging

# Set up basic configuration for production-level logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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

            try:
                session_data = self.__sessions_db.get_quiz_session(
                    session_id=session_id
                )
            except Exception as e:
                # Log only the critical error to alert production
                logging.error(
                    f"Failed to retrieve session data for session_id {session_id}: {str(e)}"
                )
                raise HTTPException(status_code=500, detail="Internal server error.")

            if session_data is None:
                raise HTTPException(status_code=404, detail="Session ID not found.")

            try:
                quiz_id = session_data["redirectPlatformParams"]["id"]
                start_date = session_data["startDate"]
                end_date = session_data["endDate"]
                data = self.__quiz_db.get_live_quiz_stats(
                    quiz_id=quiz_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                logging.error(
                    f"Failed to retrieve quiz stats for quiz_id {quiz_id}: {str(e)}"
                )
                raise HTTPException(status_code=500, detail="Internal server error.")

            try:
                return self._templates.TemplateResponse(
                    "live_session_report.html",
                    {"request": request, "session_id": session_id, "data": data},
                )
            except TemplateError as e:
                logging.error(
                    f"Template rendering error for session_id {session_id}: {str(e)}"
                )
                raise HTTPException(status_code=500, detail="Template rendering error.")

        @api_router.get("/live_quiz_report/{quiz_id}")
        def get_live_quiz_report(request: Request, quiz_id: str = None):
            """
            Returns live report for a given quiz ID
            params:
                quiz_id: The quiz ID
            """
            if not quiz_id:
                raise HTTPException(status_code=400, detail="Quiz ID is required.")

            try:
                data = self.__quiz_db.get_live_quiz_stats(quiz_id=quiz_id)
            except Exception as e:
                logging.error(
                    f"Failed to retrieve quiz stats for quiz_id {quiz_id}: {str(e)}"
                )
                raise HTTPException(status_code=500, detail="Internal server error.")

            if not data:
                raise HTTPException(
                    status_code=404, detail="Quiz not found with provided Quiz ID."
                )

            try:
                return self._templates.TemplateResponse(
                    "live_session_report.html",
                    {"request": request, "session_id": "", "data": data},
                )
            except TemplateError as e:
                logging.error(
                    f"Template rendering error for quiz_id {quiz_id}: {str(e)}"
                )
                raise HTTPException(status_code=500, detail="Template rendering error.")

        return api_router
