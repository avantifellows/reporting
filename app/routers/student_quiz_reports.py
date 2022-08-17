from fastapi import APIRouter
from fastapi import HTTPException

from models.student_quiz_report import CreateStudentQuizReportModel, StudentQuizReportController


class StudentQuizReportsRouter:
    def __init__(self, student_quiz_reports_controller: StudentQuizReportController) -> None:
        self.__student_quiz_reports_controller = student_quiz_reports_controller

    @property
    def router(self):
        api_router = APIRouter(prefix='/student_quiz_reports', tags=['student_quiz_reports'])
        
        @api_router.get('/')
        def index_route():
            return 'Hello! Welcome to student_quiz_reports index route'

        @api_router.post('/create')
        def create_student_quiz_report(report_data: CreateStudentQuizReportModel):
            return self.__student_quiz_reports_controller.create_student_quiz_report(report_data)

        @api_router.get('/get')
        def get_student_quiz_report(student_id: str = None, quiz_id: str = None):
            if student_id == None or quiz_id == None:
                raise HTTPException(status_code=400, detail='Both student_id annd quiz_id have to be specified')
            try:
                return self.__student_quiz_reports_controller.get_student_quiz_report(student_id, session_id)
            except KeyError:
                raise HTTPException(status_code=400, detail='No student_quiz_report found')
                

        @api_router.get('/all')
        def get_all():
            return self.__student_quiz_reports_controller.get_all()

        return api_router