
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates



class ReportsRouter:

    def __init__(self) -> None:
        self.templates = Jinja2Templates(directory="templates")

    @property
    def router(self):
        api_router = APIRouter(prefix='/student_quiz_reports', tags=['student_quiz_reports'])
        
        @api_router.get('/')
        def index_route():
            return 'Welcome to all reports Index'

        @api_router.get('/student_quiz_report/{report_id}')
        def student_quiz_report(request: Request, report_id: str ):
            return self.templates.TemplateResponse("item.html", {"request": request, "id": report_id})

        return api_router