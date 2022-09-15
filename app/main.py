from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from internal.db import initialize_db

from models.student_quiz_report import StudentQuizReportController
from models.quiz_report import QuizReportController
from db.reports_db import ReportsDB
from routers.reports import ReportsRouter

from fastapi.staticfiles import StaticFiles

app = FastAPI()

origins = [
    "http://localhost:5050",
    "https://report-staging.avantifellows.org",
    "https://reporting.avantifellows.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

db = initialize_db()


reports_db = ReportsDB(db)
student_quiz_reports_controller = StudentQuizReportController(reports_db)
quiz_reports_controller = QuizReportController(reports_db)
# student_quiz_reports_router = StudentQuizReportsRouter(student_quiz_reports_controller)

reports_router = ReportsRouter(student_quiz_reports_controller, quiz_reports_controller)

# app.include_router(student_quiz_reports_router.router)
app.include_router(reports_router.router)


@app.get("/")
def index():
    return "Hello World! Welcome to Reporting Engine!"


handler = Mangum(app)
