import os
import tempfile
import pypdf
import docx2txt
from typing import Optional


class ResumeParser:
    def extract_text_from_bytes(self, file_bytes: bytes, extension: str) -> str:
        """Extract text from file bytes based on file extension"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name

        try:
            if extension == ".pdf":
                return self.extract_text_from_pdf(temp_file_path)
            elif extension == ".docx":
                return self.extract_text_from_docx(temp_file_path)
            else:
                raise ValueError("Unsupported file format")
        finally:
            os.remove(temp_file_path)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files"""
        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise RuntimeError(f"Error extracting PDF text: {str(e)}")

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            raise RuntimeError(f"Error extracting DOCX text: {str(e)}")
