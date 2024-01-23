from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from db.sessions_db import SessionsDB
from db.quiz_db import QuizDB
from routers.session_quiz_reports import SessionQuizReportsRouter

from internal.db import initialize_quiz_db, initialize_reports_db

from db.reports_db import ReportsDB
from routers.student_quiz_reports import StudentQuizReportsRouter

from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

reports_db = initialize_reports_db()
quiz_db = initialize_quiz_db()

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


student_quiz_reports_db = ReportsDB(reports_db)
quiz_db = QuizDB(quiz_db)
sessions_db = SessionsDB()
student_quiz_reports_router = StudentQuizReportsRouter(
    reports_db=student_quiz_reports_db
)
quiz_reports_router = SessionQuizReportsRouter(quiz_db=quiz_db, sessions_db=sessions_db)

app.include_router(student_quiz_reports_router.router)
app.include_router(quiz_reports_router.router)


@app.get("/")
def index():
    return "Hello World! Welcome to Reporting Engine!"


handler = Mangum(app)
