
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from collections import OrderedDict

from models.student_quiz_report import StudentQuizReportController

ROW_NAMES = OrderedDict()
ROW_NAMES = {
    "marks_scored": "Marks",
    "num_skipped": "Unattempted",
    "num_wrong": "Wrong Answers",
    "num_correct": "Correct Answers",
    "percentage": "Percentage",
    "highest_test_score": "Topper Marks",
    "percentile": "Percentile",
    "rank": "Rank"
}

class ReportsRouter:

    def __init__(self, student_quiz_reports_controller: StudentQuizReportController) -> None:
        self.__student_quiz_reports_controller = student_quiz_reports_controller
        self._templates = Jinja2Templates(directory="app/templates")

    @property
    def router(self):
        api_router = APIRouter(prefix='/reports', tags=['reports'])

        def _parse_section_data(section=None):
            section["name"] = section["user_id-section"].split("#")[1].capitalize()
            section_report = {}
            section_report["name"] = "Performance - " + section["name"].capitalize()
            table_data = {}
            for row in ROW_NAMES:
                table_data[ROW_NAMES[row]] = section[row]
            section_report["table_data"] = table_data
            return section_report
        
        @api_router.get('/student_quiz_report/{session_id}/{user_id}')
        def student_quiz_report(request: Request, session_id: str, user_id: str):
            if session_id == None or user_id == None:
                raise HTTPException(status_code=400, detail='Session ID and User ID have to be specified')
            try:
                data = self.__student_quiz_reports_controller.get_student_quiz_report(session_id=session_id, user_id=user_id)
            except KeyError:
                raise HTTPException(status_code=400, detail='No student_quiz_report found')
            report_data = {}
            report_data["student_name"] = ""
            report_data["student_id"] = data[0]["user_id"]
            
            section_reports = []
            overall_performance = {}
            for section in data:
                parsed_section_data = _parse_section_data(section)
                if (section["section"] == "overall"):
                    overall_performance = parsed_section_data
                    report_data["percentage"] = parsed_section_data["table_data"]["Percentage"]
                    report_data["test_name"] = section["test_name"]
                    report_data["test_date"] = section["start_date"]
                else:
                    section_reports.append(parsed_section_data)
            report_data["overall_performance"] = overall_performance
            report_data["section_reports"] = section_reports
            return self._templates.TemplateResponse("student_quiz_report.html", {"request": request, "report_data": report_data})

        return api_router

 