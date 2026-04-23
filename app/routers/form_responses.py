from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import asyncio
from auth import verify_launch_token
from db.form_responses_db import FormResponsesDB
from utils.pdf_converter import convert_template_to_pdf
from utils.llm_summary import generate_theme_summary

REPORT_LAUNCH_COOKIE_MAX_AGE = 15 * 60


class FormResponsesRouter:
    """
    Router class for handling Form Responses related endpoints.
    """

    def __init__(self, form_responses_db: FormResponsesDB) -> None:
        self.__form_responses_db = form_responses_db
        self._templates = Jinja2Templates(directory="templates")

    @property
    def router(self):
        api_router = APIRouter(prefix="/reports", tags=["form_responses"])

        def _resolve_report_user_id(
            user_id: Optional[str], launch_token: Optional[str]
        ) -> str:
            if user_id:
                return user_id

            payload = verify_launch_token(launch_token, expected_audience="report")
            token_data = payload.get("data", {})
            canonical_user_id = token_data.get("user_id") or payload.get("id")

            if not canonical_user_id:
                raise HTTPException(status_code=401, detail="Missing user in launch token")

            return str(canonical_user_id)

        def _get_launch_cookie_name(prefix: str, session_id: str) -> str:
            safe_session_id = "".join(
                char if char.isalnum() else "_" for char in session_id
            )
            return f"{prefix}_{safe_session_id}"

        def _set_launch_cookie(response, request: Request, cookie_name: str, token: str, path: str):
            response.set_cookie(
                key=cookie_name,
                value=token,
                max_age=REPORT_LAUNCH_COOKIE_MAX_AGE,
                httponly=True,
                secure=request.url.scheme == "https",
                samesite="lax",
                path=path,
            )

        def _clean_query_string(request: Request) -> str:
            params = [
                (key, value)
                for key, value in request.query_params.multi_items()
                if key != "launchToken"
            ]
            if not params:
                return ""

            from urllib.parse import urlencode

            return urlencode(params, doseq=True)

        def _redirect_with_launch_cookie(
            request: Request,
            session_id: str,
            launch_token: str,
            cookie_prefix: str,
            clean_path: str,
        ) -> RedirectResponse:
            verify_launch_token(launch_token, expected_audience="report")
            redirect_url = clean_path
            query_string = _clean_query_string(request)
            if query_string:
                redirect_url = f"{redirect_url}?{query_string}"

            response = RedirectResponse(url=redirect_url, status_code=302)
            cookie_name = _get_launch_cookie_name(cookie_prefix, session_id)
            _set_launch_cookie(response, request, cookie_name, launch_token, clean_path)
            return response

        def _get_report_launch_token(
            request: Request,
            session_id: str,
            launch_token: Optional[str],
            cookie_prefix: str,
        ) -> str:
            if launch_token:
                return launch_token

            cookie_name = _get_launch_cookie_name(cookie_prefix, session_id)
            token = request.cookies.get(cookie_name)
            if not token:
                raise HTTPException(status_code=401, detail="Missing launch token")
            return token

        @api_router.get("/form_responses/{session_id}")
        async def get_form_responses_with_token(
            request: Request,
            session_id: str,
            launchToken: Optional[str] = None,
            format: Optional[str] = None,
            debug: bool = False,
        ):
            if launchToken:
                return _redirect_with_launch_cookie(
                    request=request,
                    session_id=session_id,
                    launch_token=launchToken,
                    cookie_prefix="form_responses_launch",
                    clean_path=f"/reports/form_responses/{session_id}",
                )

            resolved_user_id = _resolve_report_user_id(
                None,
                _get_report_launch_token(
                    request=request,
                    session_id=session_id,
                    launch_token=launchToken,
                    cookie_prefix="form_responses_launch",
                ),
            )
            return await get_form_responses(
                request=request,
                session_id=session_id,
                user_id=resolved_user_id,
                format=format,
                debug=debug,
            )

        @api_router.get("/form_responses/{session_id}/{user_id}")
        async def get_form_responses(
            request: Request,
            session_id: str,
            user_id: str,
            format: Optional[str] = None,
            debug: bool = False,
        ):
            """
            Get form responses for a specific user and session.

            Args:
                request (Request): The request object.
                session_id (str): The session ID.
                user_id (str): The user ID.
                format (str, optional): The format of the report. If "pdf", returns a PDF. Defaults to None.
                debug (bool): If True and format is "pdf", returns the HTML that would be sent to PDF service.

            Returns:
                TemplateResponse: The form responses template response.
                StreamingResponse: A PDF response if format=pdf.
            """
            try:
                # Get form responses from database
                form_responses = self.__form_responses_db.get_form_responses(
                    session_id, user_id
                )

                if not form_responses:
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

                # Process and group form responses by theme
                responses_by_theme = {}
                overall_question_number = 0

                for idx, response in enumerate(form_responses):
                    overall_question_number += 1
                    theme = response.get("question_set_title", "Unknown Theme")
                    question_text = response.get("question_text", "")
                    question_priority = response.get("priority", "")
                    user_response_labels = response.get("user_response_labels", "")
                    is_answered = response.get("is_answered", False)

                    # Display "None" if not answered, otherwise show the response labels
                    display_response = (
                        user_response_labels
                        if is_answered and user_response_labels
                        else "None"
                    )

                    if theme not in responses_by_theme:
                        responses_by_theme[theme] = []

                    responses_by_theme[theme].append(
                        {
                            "question_number": overall_question_number,
                            "question_text": question_text,
                            "user_response": display_response,
                            "question_priority": question_priority,
                        }
                    )

                # Convert to list format for template and generate AI summaries
                themed_responses = []

                # Generate summaries only for themes with high priority questions
                summary_tasks = []
                themes_list = list(responses_by_theme.items())
                themes_with_high_priority = []

                for theme, responses in themes_list:
                    # Check if this theme has any high priority questions
                    has_high_priority = any(
                        r.get("question_priority") == "high" for r in responses
                    )

                    if has_high_priority:
                        themes_with_high_priority.append((theme, responses))
                        task = generate_theme_summary(theme, responses, user_id)
                        summary_tasks.append(task)

                # Wait for all summaries to complete
                summaries = await asyncio.gather(*summary_tasks, return_exceptions=True)

                # Build themed_responses with summaries
                summary_index = 0
                for theme, responses in themes_list:
                    # Check if this theme has high priority questions
                    has_high_priority = any(
                        r.get("question_priority") == "high" for r in responses
                    )

                    # Get summary only if theme has high priority questions
                    if has_high_priority:
                        summary = None
                        if summary_index < len(summaries):
                            summary = (
                                summaries[summary_index]
                                if not isinstance(summaries[summary_index], Exception)
                                else None
                            )
                            summary_index += 1

                        themed_responses.append(
                            {
                                "theme": theme,
                                "responses": responses,
                                "question_count": len(responses),
                                "ai_summary": summary,
                            }
                        )

                # Get basic info from first response
                first_response = form_responses[0]
                report_data = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "test_name": first_response.get("test_name", "Form Response"),
                    "start_date": first_response.get("start_date", ""),
                    "themed_responses": themed_responses,
                    "total_questions": len(form_responses),
                }

                template_response = self._templates.TemplateResponse(
                    "form_responses.html",
                    {"request": request, "report_data": report_data},
                )

                if format == "pdf":
                    return convert_template_to_pdf(template_response, debug=debug)

                return template_response

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

        return api_router
