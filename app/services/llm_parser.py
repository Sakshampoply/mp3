import ollama
import json
import re
import traceback
from typing import Dict, Any
from app.core.config import settings


class LLMParser:
    """
    Handles resume parsing using LLM models via Ollama
    """

    EXTRACTION_PROMPT = """Return ONLY valid JSON without any formatting, markdown, or explanations. Structure:
{{
  "name": "full name",
  "email": "email",
  "phone": "phone",
  "skills": ["list", "of", "technical", "skills"],
  "experience_years": number,
  "education": [{{"degree": "...", "field": "...", "institute": "..."}}]
}}

Resume content: {text}"""

    def __init__(self):
        self.extraction_model = settings.EXTRACTION_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from resume text using LLM
        Returns:
            Dict: Parsed data or error information
        """
        try:
            if not text.strip():
                return {"error": "Empty resume content"}

            # Truncate text to avoid context window issues
            processed_text = text[:3000].replace('"', "'")

            response = ollama.chat(
                model=self.extraction_model,
                messages=[
                    {
                        "role": "user",
                        "content": self.EXTRACTION_PROMPT.format(text=processed_text),
                    }
                ],
                options={"timeout": 120},  # 2 minute timeout
            )

            raw_response = response["message"]["content"]

            # Extract JSON using regex to handle markdown wrappers
            json_str = re.search(r"\{(\n|.)*\}", raw_response).group()

            # Smart cleaning without over-escaping
            json_str = (
                json_str.replace("'", '"')
                .replace("\\n", "")
                .replace("\\", "")
                .replace("None", "0")
                .replace("null", "0")
                .replace(" experience ", "experience_years")
            )

            # Validate and repair numeric fields
            json_str = re.sub(
                r'"experience_years":\s*([^0-9].*?)(,|\})',
                r'"experience_years": 0\2',
                json_str,
            )

            # Parse with relaxed JSON decoder
            parsed_data = json.loads(json_str, strict=False)

            # Final validation
            if not isinstance(parsed_data.get("experience_years", 0), (int, float)):
                parsed_data["experience_years"] = 0

            return parsed_data

        except Exception as e:
            return {
                "error": f"Enhanced parser error: {str(e)}",
                "raw_response": raw_response,
                "json_attempt": json_str,
            }
