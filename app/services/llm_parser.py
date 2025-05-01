import logging
import re
from typing import Any, Dict

import json5
import ollama

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMParser:
    """
    Handles resume parsing using LLM models via Ollama with robust JSON handling
    """

    EXTRACTION_PROMPT = """Return VALID JSON with these rules:
- Use double quotes for all strings
- Escape internal double quotes with \\
- No trailing commas
- experience_years must be a number
Structure:
{{
  "name": "Full Name",
  "email": "email",
  "phone": "phone",
  "skills": ["skill1", "skill2"],
  "experience_years": 2,
  "education": [{{"degree": "...", "institute": "..."}}]
}}

Resume content: {text}"""

    def __init__(self):
        self.extraction_model = settings.EXTRACTION_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

    def extract_entities(self, text: str) -> dict[str, Any]:
        """Extract structured data from resume text with error resilience"""
        try:
            if not text.strip():
                return {"error": "Empty resume content"}

            # Clean input text
            clean_text = self._sanitize_input(text[:4000])

            response = ollama.chat(
                model=self.extraction_model,
                messages=[
                    {
                        "role": "user",
                        "content": self.EXTRACTION_PROMPT.format(text=clean_text),
                    }
                ],
                options={"timeout": 300},
            )

            parsed_data = self._parse_llm_response(response["message"]["content"])

            if "education" in parsed_data:
                if isinstance(parsed_data["education"], list):
                    parsed_data["education"] = [
                        e if isinstance(e, dict) else {"degree": str(e)}
                        for e in parsed_data["education"]
                    ]
            return parsed_data

        except Exception as e:
            logger.error(f"LLM Parser error: {str(e)}", exc_info=True)
            return {"error": f"Processing error: {str(e)}"}

    def _sanitize_input(self, text: str) -> str:
        """Clean problematic characters from input text"""
        return (
            text.replace("\x00", "")  # Remove null bytes
            .replace("\\", "")  # Remove backslashes
            .replace("“", '"')  # Replace smart quotes
            .replace("”", '"')
            .replace("'", "")
            .replace("\t", " ")  # Replace tabs
        )

    def _parse_llm_response(self, raw_response: str) -> dict[str, Any]:
        """Parse and validate LLM JSON response"""
        json_str = ""
        try:
            # Extract JSON using improved pattern
            json_match = re.search(r"\{[\s\S]*\}", raw_response)
            if not json_match:
                return {"error": "No JSON found in response"}

            json_str = json_match.group()

            # Fix common JSON issues using regex
            json_str = re.sub(r",\s*([}\]])", r"\1", json_str)  # Trailing commas
            json_str = re.sub(r'\\"(.*?)\\"', r'"\1"', json_str)  # Over-escaped quotes
            json_str = (
                json_str.replace("'", '"')
                .replace("True", "true")
                .replace("False", "false")
                .replace("None", "null")
                .replace('\\"', '"')
                .replace('"s ', "'s ")  # Handle possessives
            )

            # Attempt parsing
            parsed = json5.loads(json_str)

            # Normalize experience field
            exp_years = parsed.get("experience_years", 0)
            if isinstance(exp_years, list):
                parsed["experience_years"] = len(exp_years)
            elif isinstance(exp_years, (int, float)):
                parsed["experience_years"] = max(0, exp_years)
            else:
                parsed["experience_years"] = 0

            # Validate required fields
            if not parsed.get("name") or not parsed.get("email"):
                return {"error": "Missing required fields (name/email)"}

            return parsed

        except ValueError as e:
            logger.error(f"JSON5 parse error: {str(e)}\nAttempted JSON: {json_str}")
            return {
                "error": f"JSON parsing failed: {str(e)}",
                "raw_response": raw_response,
                "json_attempt": json_str,
            }
        except Exception as e:
            logger.error(f"Unexpected parsing error: {str(e)}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "raw_response": raw_response,
            }
