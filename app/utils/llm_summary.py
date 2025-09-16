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
            # Filter for high-priority responses only
            high_priority_responses = [
                r
                for r in responses
                if r.get("user_response")
                and r["user_response"] != "None"
                and r.get("question_priority") == "high"
            ]

            # Only use high-priority responses, limit to 8
            valid_responses = high_priority_responses[:8]

            if not valid_responses:
                return f"No high priority responses provided for {theme} section."

            # Prepare data for LLM
            response_data = [
                {
                    "question": r["question_text"],
                    "answer": r["user_response"],
                    "priority": r.get("question_priority", "standard"),
                }
                for r in valid_responses
            ]

            prompt = self._create_summary_prompt(theme, response_data, user_id)

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
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
Analyze responses{user_context} for "{theme}" section:

{json.dumps(response_data, indent=2, ensure_ascii=False)}

Provide a clear summary in 2-3 short, broken sentences that focus on the high priority questions. Each sentence should be concise and give specific insights about the student's responses. Use constructive educational language.
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
