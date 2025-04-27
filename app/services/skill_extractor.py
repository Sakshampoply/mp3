from app.core.config import settings
import ollama
import json


class SkillExtractor:
    def __init__(self):
        self.model = settings.EXTRACTION_MODEL

    def extract_skills(self, text: str) -> list[str]:
        """Extract skills from job description text"""
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extract technical skills as a JSON array from this text:
                    {text[:3000]}
                    Return ONLY the array without additional formatting.""",
                    }
                ],
            )
            return json.loads(response["message"]["content"])
        except Exception as e:
            return []
