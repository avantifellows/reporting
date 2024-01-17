from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from internal.db import initialize_db

from app.models.student_quiz_reports import StudentQuizReportController
from db.student_quiz_reports_db import StudentQuizReportsDB
from routers.reports import StudentQuizReportsRouter

from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

db = initialize_db()

origins = [
    "http://localhost:3000",  # gurukul localhost
    "https://reports.avantifellows.org",
    "https://reports-staging.avantifellows.org",
    "https://main.d2gowi7rh3vzhn.amplifyapp.com",
    "https://gurukul.avantifellows.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


student_quiz_reports_db = StudentQuizReportsDB(db)
student_quiz_reports_controller = StudentQuizReportController(student_quiz_reports_db)
student_level_reports_router = StudentQuizReportsRouter(student_quiz_reports_controller)

reports_router = StudentQuizReportsRouter(student_quiz_reports_controller)
app.include_router(reports_router.router)


@app.get("/")
def index():
    return "Hello World! Welcome to Reporting Engine!"


handler = Mangum(app)
