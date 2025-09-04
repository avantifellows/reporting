from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from db.sessions_db import SessionsDB
from db.quiz_db import QuizDB
from db.bq_db import BigQueryDB
from routers.session_quiz_reports import SessionQuizReportsRouter

from internal.db import initialize_quiz_db, initialize_reports_db, initialize_bigquery

from db.reports_db import ReportsDB
from db.form_responses_db import FormResponsesDB
from routers.student_quiz_reports import StudentQuizReportsRouter
from routers.form_responses import FormResponsesRouter

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from routers import futures_college_predictor, futures

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

reports_db = initialize_reports_db()
quiz_db = initialize_quiz_db()
bq_db = initialize_bigquery()

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
form_responses_db = FormResponsesDB(reports_db)
quiz_db = QuizDB(quiz_db)
bq_db = BigQueryDB(bq_db)
sessions_db = SessionsDB()

student_quiz_reports_router = StudentQuizReportsRouter(
    reports_db=student_quiz_reports_db, bq_db=bq_db
)
form_responses_router = FormResponsesRouter(form_responses_db=form_responses_db)
quiz_reports_router = SessionQuizReportsRouter(quiz_db=quiz_db, sessions_db=sessions_db)

app.include_router(student_quiz_reports_router.router)
app.include_router(form_responses_router.router)
app.include_router(quiz_reports_router.router)
app.include_router(futures_college_predictor.router)
app.include_router(futures.router)

# Setup templates
templates = Jinja2Templates(directory="templates")


@app.get("/")
def index():
    return "Hello World! Welcome to Reporting Engine!"


handler = Mangum(app)
