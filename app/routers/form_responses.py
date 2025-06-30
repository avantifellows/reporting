from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Optional
from db.form_responses_db import FormResponsesDB


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
        def get_form_responses(
            request: Request,
            session_id: str,
            user_id: str,
            format: Optional[str] = None,
        ):
            """
            Get form responses for a specific user and session.
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

                # Process the form responses for display
                processed_responses = []

                for idx, response in enumerate(form_responses):
                    question_number = idx + 1
                    question_set_title = response.get("question_set_title", "")
                    question_text = response.get("question_text", "")
                    user_response_labels = response.get("user_response_labels", "")
                    is_answered = response.get("is_answered", False)

                    # Display "None" if not answered, otherwise show the response labels
                    display_response = (
                        user_response_labels
                        if is_answered and user_response_labels
                        else "None"
                    )

                    processed_responses.append(
                        {
                            "question_number": question_number,
                            "question_set_title": question_set_title,
                            "question_text": question_text,
                            "user_response": display_response,
                        }
                    )

                # Get basic info from first response
                first_response = form_responses[0]
                report_data = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "test_name": first_response.get("test_name", "Form Response"),
                    "start_date": first_response.get("start_date", ""),
                    "responses": processed_responses,
                    "total_questions": len(processed_responses),
                }

                return self._templates.TemplateResponse(
                    "form_responses.html",
                    {"request": request, "report_data": report_data},
                )

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

        return api_router
