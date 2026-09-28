import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
try:
    from app.api.deps import get_current_user, CurrentUser
    from app.services.job_extractor import JobExtractor
except ImportError:
    from backend.app.api.deps import get_current_user, CurrentUser
    from backend.app.services.job_extractor import JobExtractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/py", tags=["jobs"])

class JobExtractRequest(BaseModel):
    job_text: Optional[str] = None
    job_description: Optional[str] = None
    url: Optional[str] = None

@router.post("/extract-job")
async def extract_job(request: JobExtractRequest, current_user: CurrentUser = Depends(get_current_user)):
    logger.info("[AI Extraction] Request received at /api/py/extract-job")
    text_content = request.job_text or request.job_description or ""
    if not text_content and request.url:
        text_content = f"Job listing link: {request.url}"

    if not text_content.strip():
        logger.warning("[AI Extraction] Rejected empty job description text")
        raise HTTPException(status_code=400, detail="Job description text is required")

    try:
        extracted = JobExtractor.extract_job_details(text_content)
        logger.info("[AI Extraction] Returning response to frontend")
        return extracted
    except Exception as e:
        logger.error(f"[AI Extraction] Endpoint exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI extraction internal server error: {str(e)}")

