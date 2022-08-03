import uvicorn
from fastapi import FastAPI

from internal.db import initialize_db

from models.student_quiz_report import StudentQuizReportController
from db.student_quiz_reports_db import StudentQuizReportsDB
from routers.student_quiz_reports import StudentQuizReportsRouter
from routers.reports import ReportsRouter

app = FastAPI()


db = initialize_db()


student_quiz_reports_db = StudentQuizReportsDB(db)
student_quiz_reports_controller = StudentQuizReportController(student_quiz_reports_db)
student_quiz_reports_router = StudentQuizReportsRouter(student_quiz_reports_controller)
reports_router = ReportsRouter(student_quiz_reports_controller)

app.include_router(student_quiz_reports_router.router)
app.include_router(reports_router.router)



@app.get('/')
def index():
    return 'Hello World!'

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5050, log_level="info", reload=True)