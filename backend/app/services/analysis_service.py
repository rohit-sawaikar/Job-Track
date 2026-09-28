from fastapi import HTTPException
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.matching_engine import MatchingEngine
from app.schemas.analysis import AnalysisCreateRequest, AnalysisResponse
from typing import List, Dict, Any, Optional

class AnalysisService:
    def __init__(self):
        self.analysis_repo = AnalysisRepository()
        self.resume_repo = ResumeRepository()
        self.matching_engine = MatchingEngine()

    def analyze_and_save(self, user_id: str, request: AnalysisCreateRequest) -> Dict[str, Any]:
        # 1. Fetch target resume metadata & verify ownership
        resume = None
        if request.resume_id:
            resume = self.resume_repo.get_resume_by_id(request.resume_id, user_id)
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found or access denied")
        
        resume_name = resume.get('name', 'Candidate Resume') if resume else 'Candidate Resume'
        resume_text = (resume.get('content_text') if resume else None) or f"Resume: {resume_name}"
        candidate_skills = (resume.get('skills') if resume else None) or []
        if not candidate_skills and resume:
            parsed = resume.get('parsed_data') or {}
            candidate_skills = parsed.get('extracted_skills') or []

        # 2. Execute 2-stage matching engine in Python
        analysis_data = self.matching_engine.analyze_resume_against_job(
            resume_text=resume_text,
            extracted_skills=candidate_skills,
            job_title=request.job_title or "Target Position",
            company=request.company or "Company",
            job_description=request.raw_job_text,
            required_skills=[],
            preferred_skills=[]
        )



        # 3. Persist analysis to database
        record = {
            'user_id': user_id,
            'job_id': request.job_id,
            'resume_id': request.resume_id,
            'match_score': analysis_data.get('match_score', 75),
            'recommendation_rating': analysis_data.get('recommendation_rating', 'Possible Match'),
            'skills_match_percent': analysis_data.get('skills_match_percent', 70),
            'experience_match_percent': analysis_data.get('experience_match_percent', 75),
            'education_match_percent': analysis_data.get('education_match_percent', 80),
            'seniority_match_percent': analysis_data.get('seniority_match_percent', 75),
            'required_skills_found': analysis_data.get('required_skills_found', []),
            'missing_required_skills': analysis_data.get('missing_required_skills', []),
            'preferred_skills_found': analysis_data.get('preferred_skills_found', []),
            'missing_preferred_skills': analysis_data.get('missing_preferred_skills', []),
            'strong_matches': analysis_data.get('strong_matches', []),
            'weak_areas': analysis_data.get('weak_areas', []),
            'skill_gaps': analysis_data.get('skill_gaps', []),
            'interview_readiness': analysis_data.get('interview_readiness', 'Medium'),
            'recommendations': analysis_data.get('recommendations', []),
            'short_summary': analysis_data.get('short_summary', 'Analysis complete.'),
            'job_title': request.job_title,
            'company': request.company,
        }

        saved_record = self.analysis_repo.save_analysis(user_id, record)
        final_result = dict(analysis_data)
        if isinstance(saved_record, dict):
            final_result.update({k: v for k, v in saved_record.items() if v is not None})
        return final_result


    def get_user_analyses(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.analysis_repo.get_user_analyses(user_id, limit)
