from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Optional
import asyncio
from db.form_responses_db import FormResponsesDB
from utils.pdf_converter import convert_template_to_pdf
from utils.llm_summary import generate_theme_summary


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
                    raise HTTPException(
                        status_code=404, detail="No form responses found"
                    )

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
                    summary = None
                    if has_high_priority and summary_index < len(summaries):
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
