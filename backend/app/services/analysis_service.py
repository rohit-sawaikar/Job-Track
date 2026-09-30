from fastapi import HTTPException
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.matching_engine import MatchingEngine
from app.schemas.analysis import AnalysisCreateRequest, AnalysisResponse
from typing import List, Dict, Any, Optional

try:
    from app.services.resume_parser import ResumeParser
except ImportError:
    from backend.app.services.resume_parser import ResumeParser

class AnalysisService:
    def __init__(self):
        self.analysis_repo = AnalysisRepository()
        self.resume_repo = ResumeRepository()
        self.matching_engine = MatchingEngine()
        self.parser = ResumeParser()

    def analyze_and_save(self, user_id: str, request: AnalysisCreateRequest) -> Dict[str, Any]:
        # Validate job description
        raw_jd = (request.raw_job_text or "").strip()
        if not raw_jd:
            raise HTTPException(status_code=400, detail="Job description text is required for analysis")

        # 1. Fetch target resume metadata & verify ownership
        resume = None
        resume_text = ""
        candidate_skills = []
        candidate_name = "Candidate"

        if request.resume_id:
            resume = self.resume_repo.get_resume_by_id(request.resume_id, user_id)
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found or access denied")
            
            # Fetch real resume file bytes from Supabase storage
            file_path = resume.get("file_path")
            file_type = (resume.get("file_type") or "pdf").lower()
            if file_path:
                try:
                    file_bytes = self.resume_repo.download_file_from_storage("resumes", file_path)
                    if file_bytes:
                        parsed = self.parser.parse_resume_content(file_bytes, file_type)
                        resume_text = parsed.get("cleaned_text") or parsed.get("raw_text") or ""
                        candidate_skills = parsed.get("extracted_skills") or []
                        if parsed.get("candidate_name") and parsed.get("candidate_name") != "Candidate":
                            candidate_name = parsed.get("candidate_name")
                except Exception as dl_err:
                    print(f"Warning: Could not download/parse storage file for resume {request.resume_id}: {dl_err}")

        resume_name = resume.get('name', 'Candidate Resume') if resume else 'Candidate Resume'
        if not resume_text:
            resume_text = f"Resume: {resume_name}"

        # 2. Execute matching engine in Python
        analysis_data = self.matching_engine.analyze_resume_against_job(
            resume_text=resume_text,
            extracted_skills=candidate_skills,
            job_title=request.job_title or "Target Position",
            company=request.company or "Company",
            job_description=raw_jd,
            required_skills=[],
            preferred_skills=[],
            candidate_name=candidate_name
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
