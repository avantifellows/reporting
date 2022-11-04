from fastapi import FastAPI
from mangum import Mangum

from internal.db import initialize_db

from models.student_quiz_report import StudentQuizReportController
from db.student_quiz_reports_db import StudentQuizReportsDB
from routers.reports import ReportsRouter

from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

db = initialize_db()


student_quiz_reports_db = StudentQuizReportsDB(db)
student_quiz_reports_controller = StudentQuizReportController(student_quiz_reports_db)
reports_router = ReportsRouter(student_quiz_reports_controller)

reports_router = ReportsRouter(student_quiz_reports_controller)
app.include_router(reports_router.router)


@app.get("/")
def index():
    return "Hello World! Welcome to Reporting Engine!"


handler = Mangum(app)
