from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from db.quiz_db import QuizDB


class QuizReportsRouter:
    """
    Router class for handling Student Reports related endpoints.
    """

    def __init__(self, quiz_db: QuizDB) -> None:
        self.__quiz_db = quiz_db
        self._templates = Jinja2Templates(directory="templates")

    @property
    def router(self):
        api_router = APIRouter(prefix="/reports", tags=["reports"])

        @api_router.get("/live_quiz_report/{quiz_id}")
        def get_live_quiz_report(request: Request, quiz_id: str = None):
            """
            Returns live quiz report for a given quiz ID.
            """
            if not quiz_id:
                raise HTTPException(status_code=400, detail="Quiz ID is required.")
            data = self.__quiz_db.get_live_quiz_stats(quiz_id=quiz_id)
            print(data)
            return data

        return api_router
