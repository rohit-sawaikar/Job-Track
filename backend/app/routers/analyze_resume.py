import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

try:
    from app.api.deps import get_current_user, CurrentUser
    from app.services.matching_engine import MatchingEngine
    from app.services.resume_parser import ResumeParser
    from app.services.resume_service import ResumeService
    from app.services.job_service import JobService
except ImportError:
    from backend.app.api.deps import get_current_user, CurrentUser
    from backend.app.services.matching_engine import MatchingEngine
    from backend.app.services.resume_parser import ResumeParser
    from backend.app.services.resume_service import ResumeService
    from backend.app.services.job_service import JobService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/py", tags=["analyzer"])

class AnalyzeResumeRequest(BaseModel):
    resume_text: Optional[str] = None
    resume_skills: Optional[List[str]] = []
    job_title: Optional[str] = "Target Position"
    company: Optional[str] = ""
    job_description: Optional[str] = None
    raw_job_text: Optional[str] = None
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    resume_id: Optional[str] = None
    job_id: Optional[str] = None

@router.post("/analyze-resume")
async def analyze_resume(request: AnalyzeResumeRequest, current_user: CurrentUser = Depends(get_current_user)):
    jd_text = request.job_description or request.raw_job_text or ""
    job_title = request.job_title or "Target Position"
    company = request.company or ""
    req_skills = request.required_skills or []
    pref_skills = request.preferred_skills or []

    # 1. Resolve Job Metadata if job_id is provided
    if request.job_id:
        try:
            job_service = JobService()
            job_rec = job_service.get_job_by_id(request.job_id, user_id=current_user.id)
            if job_rec:
                if job_title == "Target Position" or not job_title:
                    job_title = job_rec.get("title") or job_title
                if not company:
                    company = job_rec.get("company") or company
                if not jd_text or not jd_text.strip():
                    jd_text = job_rec.get("description") or job_rec.get("requirements") or ""
                if not req_skills:
                    req_skills = job_rec.get("skills") or job_rec.get("required_skills") or []
        except Exception as job_err:
            logger.warning(f"Could not load job metadata for job_id {request.job_id}: {job_err}")

    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required for analysis")

    resume_text = request.resume_text or ""
    extracted_skills = request.resume_skills or []
    candidate_name = "Candidate"

    # 2. Retrieve & Parse Resume Content if resume_id is provided
    if request.resume_id:
        try:
            resume_service = ResumeService()
            rec = resume_service.repository.get_resume_by_id(request.resume_id, user_id=current_user.id)
            if rec:
                raw_name = rec.get("name", "")
                if raw_name:
                    # Clean up "(General)" or "(Role)" suffixes from display name
                    clean_name = raw_name.rsplit("(", 1)[0].strip() if "(" in raw_name else raw_name.strip()
                    if clean_name and clean_name.lower() != "resume":
                        candidate_name = clean_name

                db_content = rec.get("content_text")
                db_skills = rec.get("skills")

                if db_content and db_content.strip():
                    resume_text = db_content
                if db_skills and isinstance(db_skills, list) and len(db_skills) > 0:
                    extracted_skills = db_skills

                # If content_text is missing in DB schema, retrieve storage file bytes directly
                file_path = rec.get("file_path")
                file_type = rec.get("file_type") or "pdf"
                
                if (not resume_text or not resume_text.strip()) and file_path:
                    logger.info(f"Downloading resume file from storage path: {file_path}")
                    file_bytes = resume_service.repository.download_file_from_storage("resumes", file_path)
                    if file_bytes:
                        parsed = ResumeParser.parse_resume_content(file_bytes, file_type)
                        resume_text = parsed.get("cleaned_text") or parsed.get("raw_text") or ""
                        if not extracted_skills:
                            extracted_skills = parsed.get("extracted_skills") or []
                        if candidate_name == "Candidate" and parsed.get("candidate_name"):
                            candidate_name = parsed.get("candidate_name")
        except Exception as err:
            logger.error(f"Error fetching resume record {request.resume_id} for analysis: {err}")

    # Fallback parsing if resume_text is available as string but skills missing
    if resume_text and not extracted_skills:
        parsed = ResumeParser.parse_resume_content(resume_text.encode('utf-8'), 'txt')
        extracted_skills = parsed.get("extracted_skills", [])
        if candidate_name == "Candidate" and parsed.get("candidate_name"):
            candidate_name = parsed.get("candidate_name")

    # 3. Perform Evidence-Based Analysis via MatchingEngine
    try:
        analysis = MatchingEngine.analyze_resume_against_job(
            resume_text=resume_text,
            extracted_skills=extracted_skills,
            job_title=job_title,
            company=company,
            job_description=jd_text,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            candidate_name=candidate_name
        )
        return analysis
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Analysis failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

