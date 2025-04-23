import os
import re
import pypdf
import docx2txt
from typing import Dict, List, Any, Tuple
import tempfile


class ResumeParser:
    """
    A service to parse resumes in PDF and DOCX formats.
    Extracts text and basic metadata like potential skills.
    """
    def __init__(self):
        # Basic list of common technical skills to look for
        self.common_skills = {
            "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby", "golang", "rust",
            "react", "angular", "vue", "node", "django", "flask", "spring", "express", "fastapi",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "git", "ci/cd",
            "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "nosql",
            "machine learning", "deep learning", "nlp", "computer vision", "data science",
            "html", "css", "sass", "less", "jquery", "bootstrap", "tailwind",
            "rest api", "graphql", "microservices", "agile", "scrum", "jira"
        }
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from a PDF file"""
        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text content from a DOCX file"""
        try:
            text = docx2txt.process(file_path)
            return text
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text based on file type"""
        if file_path.lower().endswith(".pdf"):
            return self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract potential skills from resume text"""
        found_skills = []
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Look for common skills
        for skill in self.common_skills:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                found_skills.append(skill)
        
        return found_skills
    
    def estimate_experience_years(self, text: str) -> float:
        """
        Attempt to estimate years of experience from resume text.
        This is a basic implementation and may need refinement.
        """
        # Look for patterns like "X years of experience" or "X+ years"
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience\s+(?:of\s+)?(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+in\s+(?:the\s+)?industry',
        ]
        
        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                for match in matches:
                    try:
                        years = float(match)
                        max_years = max(max_years, years)
                    except ValueError:
                        pass
        
        return max_years
    
    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract education information from resume text.
        This is a basic implementation and may need refinement.
        """
        education = []
        
        # Look for common degree patterns
        degree_patterns = [
            r'(bachelor|master|phd|doctorate|bs|ms|ba|ma|mba|b\.s\.|m\.s\.|b\.a\.|m\.a\.|m\.b\.a\.)',
            r'(computer science|engineering|information technology|data science|business)'
        ]
        
        # This is just a basic implementation that can be improved
        for degree in degree_patterns[0].split('|'):
            if re.search(r'\b' + re.escape(degree) + r'\b', text.lower()):
                for field in degree_patterns[1].split('|'):
                    if re.search(r'\b' + re.escape(field) + r'\b', text.lower()):
                        education.append({
                            "degree": degree,
                            "field": field
                        })
        
        return education
    
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse a resume file and extract key information"""
        text = self.extract_text(file_path)
        
        if not text:
            return {
                "success": False,
                "error": "Failed to extract text from the resume"
            }
        
        # Extract metadata
        skills = self.extract_skills(text)
        experience_years = self.estimate_experience_years(text)
        education = self.extract_education(text)
        
        return {
            "success": True,
            "raw_text": text,
            "metadata": {
                "skills": skills,
                "experience_years": experience_years,
                "education": education
            }
        }
    
    def parse_resume_from_bytes(self, file_bytes: bytes, file_extension: str) -> Dict[str, Any]:
        """Parse a resume from bytes"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        
        try:
            result = self.parse_resume(temp_file_path)
            return result
        finally:
            # Remove the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)