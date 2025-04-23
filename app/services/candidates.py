from sqlalchemy.orm import Session
from typing import List, Dict, Any
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.resume import Resume, Candidate
from app.models.job import Job


class CandidateService:
    """Service to handle candidate ranking and filtering operations"""
    
    def filter_candidates_by_skill(self, db: Session, skill: str) -> List[Dict[str, Any]]:
        """Filter candidates by a specific skill"""
        # Query resumes with the given skill in their skills array
        results = db.query(Resume, Candidate).join(Candidate).filter(
            Resume.skills.contains([skill])
        ).all()
        
        return [
            {
                "resume_id": resume.id,
                "candidate_id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "skills": resume.skills
            }
            for resume, candidate in results
        ]
    
    def rank_candidates_for_job(
        self, 
        db: Session, 
        job_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Rank candidates based on their match to a specific job"""
        # Get the job
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            return []
        
        # Get all active resumes with their candidates
        resumes_with_candidates = db.query(Resume, Candidate).join(Candidate).filter(
            Resume.is_active == True
        ).all()
        
        if not resumes_with_candidates:
            return []
        
        # Calculate match scores
        ranked_candidates = []
        for resume, candidate in resumes_with_candidates:
            score = self._calculate_match_score(resume, job)
            ranked_candidates.append({
                "resume_id": resume.id,
                "candidate_id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "match_score": score,
                "skills": resume.skills,
                "matching_skills": self._get_matching_skills(resume.skills, job.skills_required)
            })
        
        # Sort by match score (descending)
        ranked_candidates.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Return top candidates
        return ranked_candidates[:limit]
    
    def _calculate_match_score(self, resume: Resume, job: Job) -> float:
        """Calculate match score between a resume and job"""
        score = 0.0
        
        # 1. Skills matching (50% weight)
        if resume.skills and job.skills_required:
            matching_skills = self._get_matching_skills(resume.skills, job.skills_required)
            if job.skills_required:
                skills_score = len(matching_skills) / len(job.skills_required)
            else:
                skills_score = 0
            score += 0.5 * skills_score
        
        # 2. Experience matching (30% weight)
        if resume.experience_years is not None and job.experience_required is not None:
            # Full points if candidate meets or exceeds required experience
            if resume.experience_years >= job.experience_required:
                experience_score = 1.0
            else:
                # Partial points based on how close they are
                experience_score = resume.experience_years / job.experience_required
                experience_score = min(1.0, experience_score)  # Cap at 1.0
            
            score += 0.3 * experience_score
        
        # 3. Education matching (20% weight) - simplified implementation
        education_score = 0.0
        if resume.education and job.education_required:
            # Simple check for any matching fields
            resume_fields = [edu.get("field", "").lower() for edu in resume.education]
            job_fields = [edu.get("field", "").lower() for edu in job.education_required]
            
            if resume_fields and job_fields:
                matches = sum(1 for field in resume_fields if any(job_field in field for job_field in job_fields))
                education_score = min(1.0, matches / len(job_fields))
        
        score += 0.2 * education_score
        
        return score
    
    def _get_matching_skills(self, candidate_skills: List[str], job_skills: List[str]) -> List[str]:
        """Get matching skills between candidate and job"""
        if not candidate_skills or not job_skills:
            return []
        
        # Case-insensitive matching
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        job_skills_lower = [skill.lower() for skill in job_skills]
        
        return [skill for skill in candidate_skills if skill.lower() in job_skills_lower]
    
    def perform_text_similarity(self, job_text: str, resume_texts: List[str]) -> List[float]:
        """
        Use TF-IDF and cosine similarity to compute text-based similarity scores
        between a job description and multiple resume texts.
        """
        if not resume_texts:
            return []
        
        # Create a corpus with job description first, followed by resumes
        corpus = [job_text] + resume_texts
        
        # Compute TF-IDF vectors
        vectorizer = TfidfVectorizer(
            stop_words='english', 
            ngram_range=(1, 2),  # Include bigrams
            max_features=5000
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            # Get the job description vector (first document)
            job_vector = tfidf_matrix[0:1]
            
            # Get resume vectors (all other documents)
            resume_vectors = tfidf_matrix[1:]
            
            # Compute cosine similarity between job and each resume
            similarities = cosine_similarity(job_vector, resume_vectors)
            
            # Return as flat list
            return similarities[0].tolist()
        except Exception as e:
            print(f"Error in text similarity calculation: {e}")
            return [0.0] * len(resume_texts)