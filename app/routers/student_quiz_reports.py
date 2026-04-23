from collections import OrderedDict
from typing import Union, Optional
from urllib.parse import unquote, quote

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, Depends
from db.reports_db import ReportsDB
from db.bq_db import BigQueryDB
from fastapi.security.api_key import APIKeyHeader
from utils.pdf_converter import convert_template_to_pdf
from utils.report_launch import (
    get_report_launch_token,
    redirect_with_launch_cookie,
    resolve_report_user_id,
    set_request_launch_token,
)

ROW_NAMES = OrderedDict()
ROW_NAMES = {
    "marks_scored": "Marks",
    "num_skipped": "Questions Skipped",
    "num_wrong": "Wrong Answers",
    "num_correct": "Correct Answers",
    "num_partially_correct": "Partially Correct",
    "percentage": "Percentage",
    "accuracy": "Accuracy",
    "highest_test_score": "Topper Marks",
    "percentile": "Percentile",
    "rank": "Rank",
    "weightage": "Weightage",
}

CHAPTER_WISE_ROW_NAMES = {
    "marks_scored": "Marks",
    "max_score": "Max Marks",
    "total_questions": "Number of Questions",
    "accuracy": "Accuracy",
    "chapter_name": "Chapter Name",
    "attempt_percentage": "Attempt Rate",
    "chapter_code": "Chapter Code",
}

QUIZ_REVIEW_URL = (
    "https://quiz.avantifellows.org/quiz/{quiz_id}"
    "?apiKey={api_key}&launchToken={launch_token}"
)
QUIZ_AF_API_KEY = "6qOO8UdF1EGxLgzwIbQN"

# https://reports.avantifellows.org/reports/student_quiz_report/Homework_Quiz_2022-08-03_62ea813210de4e9677c8ce2d/1403899102
STUDENT_QUIZ_REPORT_URL = "https://reports.avantifellows.org/reports/student_quiz_report/{session_id}/{user_id}"

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


class StudentQuizReportsRouter:
    """
    Router class for handling Student Reports related endpoints.
    """

    def __init__(self, reports_db: ReportsDB, bq_db: BigQueryDB) -> None:
        self.__reports_db = reports_db
        self.__bq_db = bq_db
        self._templates = Jinja2Templates(directory="templates")

    @property
    def router(self):
        api_router = APIRouter(prefix="/reports", tags=["reports"])

        def _parse_section_data(section=None):
            """
            Parse the section data and return a formatted section report.

            Args:
                section (dict): The section data.

            Returns:
                dict: The formatted section report.
            """
            section["name"] = section["user_id-section"].split("#")[1].capitalize()
            section_report = {}
            section_report["name"] = "Performance - " + section["name"].capitalize()
            table_data = {}

            # For main table
            for row in ROW_NAMES:
                if row in section:
                    table_data[ROW_NAMES[row]] = section[row]

            # For chapter level tables where the data exists.
            # Ignore if it doesn't exist like the "Overall section", but also
            # reports that don't have chapterwise data
            if "chapter_wise_data" in section:
                table_data["chapter_level_data"] = section["chapter_wise_data"]
            section_report["table_data"] = table_data
            return section_report

        def _get_chapter_priority_ordering(
            section_reports, chapter_to_link_map, stream
        ):
            """order chapterwise section reports based on priority"""
            updated_reports = []
            for section_report in section_reports:
                updated_section = section_report.copy()

                if (
                    "table_data" in updated_section
                    and "chapter_level_data" in updated_section["table_data"]
                    and updated_section["table_data"]["chapter_level_data"]
                ):

                    chapter_data = updated_section["table_data"]["chapter_level_data"]
                    updated_chapters = []

                    for chapter in chapter_data:
                        updated_chapter = chapter.copy()
                        chapter_name = chapter.get("chapter_name", "")

                        if "-" in chapter_name:
                            chapter_code = chapter_name.split("-")[0].strip()
                        else:
                            chapter_code = chapter_name.strip()

                        if chapter_code in chapter_to_link_map:
                            if stream == "JEE":
                                priority = chapter_to_link_map[chapter_code].get(
                                    "Priority_J", "Low"
                                )
                            elif stream == "NEET":
                                priority = chapter_to_link_map[chapter_code].get(
                                    "Priority_N", "Low"
                                )
                            updated_chapter["priority"] = priority
                        else:
                            updated_chapter["priority"] = "Low"

                        updated_chapters.append(updated_chapter)

                    # Sort chapters by priority (High > Medium > Low)
                    priority_order = {"High": 3, "Medium": 2, "Low": 1}
                    updated_chapters.sort(
                        key=lambda x: priority_order.get(x.get("priority"), 0),
                        reverse=True,
                    )

                    updated_section["table_data"][
                        "chapter_level_data"
                    ] = updated_chapters

                updated_reports.append(updated_section)

            return updated_reports

        def _get_chapter_for_revision(section_reports, chapter_to_link_map, stream):
            """Determine which chapter needs revision based on performance metrics."""
            revision_candidates = []

            for section_report in section_reports:
                if (
                    "table_data" in section_report
                    and "chapter_level_data" in section_report["table_data"]
                    and section_report["table_data"]["chapter_level_data"]
                ):

                    for chapter_data in section_report["table_data"][
                        "chapter_level_data"
                    ]:
                        chapter_name = chapter_data.get("chapter_name", "")
                        accuracy = float(chapter_data.get("accuracy", 0))
                        attempt_rate = float(chapter_data.get("attempt_percentage", 0))

                        if "-" in chapter_name:
                            chapter_code = chapter_name.split("-")[0].strip()
                            chapter_name = chapter_name.split("-")[1].strip()
                        else:
                            chapter_code = chapter_name.strip()

                        if (
                            accuracy <= 75 or attempt_rate <= 50
                        ) and chapter_code in chapter_to_link_map:
                            performance_score = accuracy + attempt_rate
                            revision_candidates.append(
                                {
                                    "chapter_name": chapter_name,
                                    "chapter_code": chapter_code,
                                    "accuracy": accuracy,
                                    "attempt_rate": attempt_rate,
                                    "performance_score": performance_score,
                                }
                            )

            if revision_candidates:
                revision_candidates.sort(key=lambda x: x["performance_score"])
                selected_chapter_code = revision_candidates[0]["chapter_code"]
                selected_chapter_name = revision_candidates[0]["chapter_name"]
                chapter_link = chapter_to_link_map.get(selected_chapter_code, "")
                if selected_chapter_code in chapter_to_link_map:
                    if stream == "JEE":
                        chapter_link = chapter_to_link_map[selected_chapter_code].get(
                            "Link_J", ""
                        )
                    elif stream == "NEET":
                        chapter_link = chapter_to_link_map[selected_chapter_code].get(
                            "Link_N", ""
                        )
                else:
                    chapter_link = ""
                return selected_chapter_name, chapter_link

            return "", ""  # selected chapter name, chapter link

        def _build_quiz_review_link(
            request: Request,
            quiz_id: str,
        ) -> Optional[str]:
            launch_token = getattr(request.state, "report_launch_token", None)
            if not launch_token:
                return None

            # Direct report -> quiz review handoff reuses the verified report token.
            # Quiz resolves canonical identity from the token and strips it from the URL after boot.
            return QUIZ_REVIEW_URL.format(
                quiz_id=quote(str(quiz_id), safe=""),
                api_key=quote(QUIZ_AF_API_KEY, safe=""),
                launch_token=quote(launch_token, safe=""),
            )

        @api_router.get("/student_reports/{user_id}")
        def get_student_reports(
            request: Request,
            user_id: str = None,
            format: Union[str, None] = None,
            debug: bool = False,
            auth_header: Optional[str] = Depends(api_key_header),
        ):
            """
            Returns all student reports for a given user ID.

            Args:
                request (Request): The request object.
                user_id (str): The user ID.
                format (str, optional): The format of the reports. Defaults to None.
                debug (bool): If True and format is "pdf", returns the HTML that would be sent to PDF service.
                auth_header (str, optional): The API key header. Defaults to None.

            Raises:
                HTTPException: If the user ID is not specified.

            Returns:
                dict: JSON response if format=json.
                TemplateResponse: HTML response otherwise.
                StreamingResponse: PDF response if format=pdf.
            """

            if user_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="User ID has to be specified",
                )

            print("Getting student reports for user ID: ", user_id)
            data = self.__reports_db.get_student_reports(user_id)
            print(data)

            # Create a structured response with student reports
            student_reports = []
            for doc in data:
                if "overall" not in doc["user_id-section"]:
                    continue
                result = {
                    "test_name": doc["test_name"],
                    "test_session_id": doc["session_id"],
                    "percentile": doc["percentile"] if "percentile" in doc else "",
                    "rank": doc["rank"] if "rank" in doc else "",
                    "report_link": STUDENT_QUIZ_REPORT_URL.format(
                        session_id=doc["session_id"], user_id=user_id
                    ),
                    "start_date": doc["start_date"],
                }
                student_reports.append(result)

            # Return JSON response if format=json
            if format is not None and format == "json":
                response = {"student_id": user_id, "reports": student_reports}
                return response

            # Return HTML or PDF response
            template_response = self._templates.TemplateResponse(
                "student_reports.html",
                {"request": request, "student_id": user_id, "reports": student_reports},
            )

            if format == "pdf":
                return convert_template_to_pdf(template_response, debug=debug)

            return template_response

        @api_router.get("/student_quiz_report/{session_id}")
        def student_quiz_report_with_token(
            request: Request,
            session_id: str,
            launchToken: Optional[str] = None,
            format: Optional[str] = None,
            debug: bool = False,
        ):
            if launchToken:
                return redirect_with_launch_cookie(
                    request=request,
                    session_id=session_id,
                    launch_token=launchToken,
                    cookie_prefix="student_quiz_report_launch",
                    clean_path=f"/reports/student_quiz_report/{session_id}",
                )

            request_launch_token = get_report_launch_token(
                request=request,
                session_id=session_id,
                launch_token=launchToken,
                cookie_prefix="student_quiz_report_launch",
            )
            _set_request_launch_token(request, request_launch_token)

            resolved_user_id = resolve_report_user_id(
                None,
                request_launch_token,
            )
            return student_quiz_report(
                request=request,
                session_id=session_id,
                user_id=resolved_user_id,
                format=format,
                debug=debug,
            )

        @api_router.get("/student_quiz_report/{session_id}/{user_id}")
        def student_quiz_report(
            request: Request,
            session_id: str,
            user_id: str,
            format: Optional[str] = None,
            debug: bool = False,
        ):
            """
            Returns a student quiz report for a given session ID and user ID.
            First checks v2 table, falls back to v1 template if not found.

            For v2 reports:
            - Default: Display version with colors (student_quiz_report_v2.html)
            - ?print=true: Print-optimized version (student_quiz_report_v2_print.html)
            - ?format=pdf: Generates PDF using print-optimized template

            Args:
                request (Request): The request object.
                session_id (str): The session ID.
                user_id (str): The user ID.
                format (str, optional): If "pdf", returns a PDF. Defaults to None.
                debug (bool): If True and format is "pdf", returns HTML instead of PDF.

            Raises:
                HTTPException: If session ID or user ID is not specified.

            Returns:
                TemplateResponse: HTML report (display or print version).
                StreamingResponse: PDF response if format=pdf.
                HTMLResponse: HTML content if format=pdf and debug=True.
            """
            if session_id is None or user_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Session ID and User ID have to be specified",
                )
            # decoding URL encoded values. As this information is coming through a URL,
            # it's possible that the strings are URL encoded.
            session_id = unquote(session_id)
            user_id = unquote(user_id)

            # Helper to render v2 template
            def render_v2_report(report):
                # Use top-level student_id for report_header.student_id
                if "report_header" in report and "student_id" in report:
                    report["report_header"]["student_id"] = report["student_id"]

                use_print = (
                    format == "pdf" or request.query_params.get("print") == "true"
                )
                template_name = (
                    "student_quiz_report_v2_print.html"
                    if use_print
                    else "student_quiz_report_v2.html"
                )
                template_response = self._templates.TemplateResponse(
                    template_name,
                    {"request": request, "report": report},
                )
                if format == "pdf":
                    return convert_template_to_pdf(template_response, debug=debug)
                return template_response

            # Step 1: Try v2 table with user_id (primary key lookup)
            try:
                v2_report = self.__reports_db.get_student_quiz_report_v2(
                    user_id, session_id
                )
                if v2_report:
                    return render_v2_report(v2_report)
            except ValueError:
                pass

            # Step 2: Try v2 table by session_id GSI, match student_id or apaar_id
            try:
                v2_report = self.__reports_db.get_student_quiz_report_v2_by_alt_id(
                    user_id, session_id
                )
                if v2_report:
                    return render_v2_report(v2_report)
            except ValueError:
                pass

            # Step 3: Fall back to v1 table
            try:
                data = self.__reports_db.get_student_quiz_report(user_id, session_id)
            except (KeyError, ValueError):
                data = []

            if len(data) == 0:
                # no data
                error_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "error_message": "No report found. Please contact admin.",
                    "status_code": 404,
                }
                template_response = self._templates.TemplateResponse(
                    "error.html", {"request": request, "error_data": error_data}
                )
                if format == "pdf":
                    return convert_template_to_pdf(template_response, debug=debug)
                return template_response

            report_data = {}
            report_data["student_name"] = ""
            test_id = data[0]["test_id"]
            user_id = data[0]["user_id"]

            report_data["student_id"] = user_id
            if "platform" in data[0] and data[0]["platform"] == "quizengine":
                review_quiz_link = _build_quiz_review_link(
                    request=request,
                    quiz_id=test_id,
                )
                if review_quiz_link:
                    report_data["test_link"] = review_quiz_link

            section_reports = []
            overall_performance = {}
            for section in data:
                parsed_section_data = _parse_section_data(section)
                if section["section"] == "overall":
                    overall_performance = parsed_section_data
                    report_data["percentage"] = parsed_section_data["table_data"][
                        "Percentage"
                    ]
                    report_data["test_name"] = section["test_name"]
                    report_data["test_date"] = section["start_date"]
                else:
                    section_reports.append(parsed_section_data)
            report_data["overall_performance"] = overall_performance
            report_data["section_reports"] = section_reports

            template_response = self._templates.TemplateResponse(
                "student_quiz_report.html",
                {"request": request, "report_data": report_data},
            )

            if format == "pdf":
                return convert_template_to_pdf(template_response, debug=debug)
            return template_response

        @api_router.get("/student_quiz_report/v3/{session_id}")
        def student_quiz_report_v3_with_token(
            request: Request,
            session_id: str,
            launchToken: Optional[str] = None,
            format: Optional[str] = None,
            debug: bool = False,
        ):
            if launchToken:
                return redirect_with_launch_cookie(
                    request=request,
                    session_id=session_id,
                    launch_token=launchToken,
                    cookie_prefix="student_quiz_report_v3_launch",
                    clean_path=f"/reports/student_quiz_report/v3/{session_id}",
                )

            request_launch_token = get_report_launch_token(
                request=request,
                session_id=session_id,
                launch_token=launchToken,
                cookie_prefix="student_quiz_report_v3_launch",
            )
            _set_request_launch_token(request, request_launch_token)

            resolved_user_id = resolve_report_user_id(
                None,
                request_launch_token,
            )
            return student_quiz_report_v3(
                request=request,
                session_id=session_id,
                user_id=resolved_user_id,
                format=format,
                debug=debug,
            )

        @api_router.get("/student_quiz_report/v3/{session_id}/{user_id}")
        def student_quiz_report_v3(
            request: Request,
            session_id: str,
            user_id: str,
            format: Optional[str] = None,
            debug: bool = False,
        ):
            """
            Returns a student quiz report v3 with a chapter recommendation.

            Args:
                request (Request): The request object.
                session_id (str): The session ID.
                user_id (str): The user ID.
                format (str, optional): The format of the report. If "pdf", returns a PDF. Defaults to None.
                debug (bool): If True and format is "pdf", returns the HTML that would be sent to PDF service.

            Raises:
                HTTPException: If session ID or user ID is not specified.

            Returns:
                TemplateResponse: The student quiz report template response.
                StreamingResponse: A PDF response if format=pdf.
                HTMLResponse: HTML content if format=pdf and debug=True.
            """
            if session_id is None or user_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Session ID and User ID have to be specified",
                )
            # decoding URL encoded values. As this information is coming through a URL,
            # it's possible that the strings are URL encoded.
            session_id = unquote(session_id)
            user_id = unquote(user_id)
            try:
                data = self.__reports_db.get_student_quiz_report(user_id, session_id)
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail="No student_quiz_report found. Unknown error occurred.",
                )

            if len(data) == 0:
                # no data
                error_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "error_message": "No report found. Please contact admin.",
                    "status_code": 404,
                }
                return self._templates.TemplateResponse(
                    "error.html", {"request": request, "error_data": error_data}
                )

            report_data = {}
            report_data["student_name"] = ""
            test_id = data[0]["test_id"]
            user_id = data[0]["user_id"]

            report_data["student_id"] = user_id
            if "platform" in data[0] and data[0]["platform"] == "quizengine":
                review_quiz_link = _build_quiz_review_link(
                    request=request,
                    quiz_id=test_id,
                )
                if review_quiz_link:
                    report_data["test_link"] = review_quiz_link

            # bigquery
            student_al_data = self.__bq_db.get_student_qualification_data(
                user_id, test_id
            )
            qualification_status = student_al_data["qualification_status"]
            marks_to_qualify = student_al_data["marks_to_qualify"]
            chapter_for_revision = student_al_data["chapter_curriculum"]
            revision_chapter_link = student_al_data["dpp_recommendation"]

            section_reports = []
            overall_performance = {}

            # determine stream: use data["stream"] if available, otherwise fallback to section-based detection
            stream = "JEE"  # default
            if len(data) > 0 and "stream" in data[0]:
                stream_mapping = {
                    "engineering": "JEE",
                    "medical": "NEET",
                    "ca": "CA",
                    "clat": "CLAT",
                }
                stream = stream_mapping.get(data[0]["stream"].lower(), "JEE")

            for section in data:
                parsed_section_data = _parse_section_data(section)
                if section["section"] == "overall":
                    overall_performance = parsed_section_data
                    report_data["percentage"] = parsed_section_data["table_data"][
                        "Percentage"
                    ]
                    report_data["test_name"] = section["test_name"]
                    report_data["test_date"] = section["start_date"]
                else:
                    section_reports.append(parsed_section_data)

            report_data["overall_performance"] = overall_performance
            report_data["section_reports"] = section_reports

            chapter_to_link_map = json.load(open("./static/chapter_to_links.json", "r"))

            report_data["section_reports"] = _get_chapter_priority_ordering(
                section_reports, chapter_to_link_map, stream
            )

            # (
            #     chapter_for_revision,
            #     report_data["revision_chapter_link"],
            # ) = _get_chapter_for_revision(section_reports, chapter_to_link_map, stream)

            exam = "JEE"
            if stream == "JEE":
                if "Advanced" in report_data["test_name"]:
                    exam = "JEE Advanced"  # bad
                else:
                    exam = "JEE Mains"
            elif stream == "NEET":
                exam = "NEET"
            elif stream == "CA":
                exam = "CA"
            elif stream == "CLAT":
                exam = "CLAT"

            # Set messages to None for CA and CLAT streams, only show for JEE/NEET
            if stream in ["CA", "CLAT"]:
                report_data["message_part_1"] = None
                report_data["message_part_2"] = None
            else:
                report_data["message_part_1"] = ""
                if qualification_status == "Qualified" or marks_to_qualify is None:
                    report_data[
                        "message_part_1"
                    ] = f"Good Job! You are on track to clear {exam}!"
                else:
                    report_data[
                        "message_part_1"
                    ] = f"Close enough! You are just {int(marks_to_qualify)} marks away from clearing {exam}."

                if chapter_for_revision != "" and chapter_for_revision is not None:
                    report_data[
                        "message_part_2"
                    ] = f"We recommend that you focus on the chapter {chapter_for_revision} for the next test."
                else:
                    report_data["message_part_2"] = None

            report_data["revision_chapter_link"] = revision_chapter_link

            template_response = self._templates.TemplateResponse(
                "student_quiz_report_v3.html",
                {"request": request, "report_data": report_data},
            )

            if format == "pdf":
                return convert_template_to_pdf(template_response, debug=debug)
            return template_response

        return api_router
