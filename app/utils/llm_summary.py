import json
import os
from typing import List, Dict, Optional
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLMSummaryGenerator:
    """Generate AI-powered summaries for form responses using OpenAI."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_section_summary(
        self, theme: str, responses: List[Dict], user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate an AI summary for a theme section based on user responses.

        Args:
            theme: The theme/section name
            responses: List of response dictionaries with question_text and user_response
            user_id: Optional user ID for personalization

        Returns:
            AI-generated summary string or None if generation fails
        """
        try:
            # Filter out empty/None responses for better analysis
            valid_responses = [
                r
                for r in responses
                if r.get("user_response") and r["user_response"] != "None"
            ]

            if not valid_responses:
                return f"No responses provided for {theme} section."

            # Prepare data for LLM
            response_data = [
                {
                    "question": r["question_text"],
                    "answer": r["user_response"],
                    "priority": r.get("question_priority", "standard"),
                }
                for r in valid_responses[
                    :10
                ]  # Limit to first 10 responses to avoid token limits
            ]

            prompt = self._create_summary_prompt(theme, response_data, user_id)

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary for theme '{theme}' (user: {user_id})")

            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary for theme '{theme}': {str(e)}")
            return None

    def _create_summary_prompt(
        self, theme: str, response_data: List[Dict], user_id: Optional[str] = None
    ) -> str:
        """Create a structured prompt for the LLM."""

        user_context = f" for student {user_id}" if user_id else ""

        prompt = f"""
Analyze the following form responses{user_context} for the "{theme}" section and provide a brief, insightful summary.

Responses:
{json.dumps(response_data, indent=2, ensure_ascii=False)}

Please provide a 2-3 sentence summary that:
1. Identifies key themes or patterns in the responses
2. Highlights any notable insights or areas of strength/concern
3. Uses encouraging, constructive language suitable for educational feedback

Keep the summary concise, actionable, and focused on learning insights.
        """.strip()

        return prompt


# Utility function for easy import
async def generate_theme_summary(
    theme: str, responses: List[Dict], user_id: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to generate a summary for a theme section.

    Args:
        theme: Theme name
        responses: List of response dictionaries
        user_id: Optional user ID

    Returns:
        AI-generated summary or None if generation fails
    """
    generator = LLMSummaryGenerator()
    return await generator.generate_section_summary(theme, responses, user_id)
