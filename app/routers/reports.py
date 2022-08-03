
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException

from models.student_quiz_report import StudentQuizReportController



class ReportsRouter:

    def __init__(self, student_quiz_reports_controller: StudentQuizReportController) -> None:
        self.__student_quiz_reports_controller = student_quiz_reports_controller
        self._templates = Jinja2Templates(directory="app/templates")

    @property
    def router(self):
        api_router = APIRouter(prefix='/reports', tags=['reports'])
        
        @api_router.get('/')
        def index_route():
            return 'Welcome to all reports Index'

        @api_router.get('/student_quiz_report/{report_id}')
        def student_quiz_report(request: Request, report_id: str):
            if report_id == None:
                raise HTTPException(status_code=400, detail='report_id has to be specified')
            try:
                report_data = self.__student_quiz_reports_controller.get_student_quiz_report(report_id=report_id)
            except KeyError:
                raise HTTPException(status_code=400, detail='No student_quiz_report found')
            report_data["score_details"]["percentage"] = "{:.2f}".format(report_data["score_details"]["score"] / report_data["score_details"]["max_marks"])
            return self._templates.TemplateResponse("student_quiz_report.html", {"request": request, "report_data": report_data})

        return api_router