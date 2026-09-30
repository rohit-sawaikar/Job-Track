from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Dict, Any, Optional
try:
    from app.api.deps import get_current_user, CurrentUser
    from app.schemas.resume import ResumeCreate, ResumeUpdate
    from app.schemas.analysis import AnalysisCreateRequest
    from app.schemas.profile import ProfileUpdate, ProfileLinkCreate, ProfileLinkUpdate
    from app.services.resume_service import ResumeService
    from app.services.analysis_service import AnalysisService
    from app.services.profile_service import ProfileService
except ImportError:
    from backend.app.api.deps import get_current_user, CurrentUser
    from backend.app.schemas.resume import ResumeCreate, ResumeUpdate
    from backend.app.schemas.analysis import AnalysisCreateRequest
    from backend.app.schemas.profile import ProfileUpdate, ProfileLinkCreate, ProfileLinkUpdate
    from backend.app.services.resume_service import ResumeService
    from backend.app.services.analysis_service import AnalysisService
    from backend.app.services.profile_service import ProfileService

# Resumes Router
resumes_router = APIRouter(prefix="/api/py/resumes", tags=["resumes"])
resume_service = ResumeService()

@resumes_router.get("", response_model=List[Dict[str, Any]])
async def get_resumes(current_user: CurrentUser = Depends(get_current_user)):
    return resume_service.get_user_resumes(current_user.id)

@resumes_router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_resume(resume_data: ResumeCreate, current_user: CurrentUser = Depends(get_current_user)):
    return resume_service.create_resume(current_user.id, resume_data)

@resumes_router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    resume_type: str = Form("General"),
    current_user: CurrentUser = Depends(get_current_user)
):
    try:
        content = await file.read()
        return resume_service.upload_resume_file(current_user.id, content, file.filename or "resume.pdf", resume_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume upload failed: {str(e)}")

@resumes_router.post("/{resume_id}/primary", response_model=Dict[str, Any])
async def set_primary_resume(resume_id: str, current_user: CurrentUser = Depends(get_current_user)):
    success = resume_service.set_primary_resume(resume_id, current_user.id)
    return {"success": success}

@resumes_router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: str, current_user: CurrentUser = Depends(get_current_user)):
    resume_service.delete_resume(resume_id, current_user.id)
    return None

# Analysis Router
analysis_router = APIRouter(prefix="/api/py/analysis", tags=["analysis"])
analysis_service = AnalysisService()

@analysis_router.post("", response_model=Dict[str, Any])
async def create_analysis(request: AnalysisCreateRequest, current_user: CurrentUser = Depends(get_current_user)):
    return analysis_service.analyze_and_save(current_user.id, request)

@analysis_router.get("", response_model=List[Dict[str, Any]])
async def get_analyses(current_user: CurrentUser = Depends(get_current_user)):
    return analysis_service.get_user_analyses(current_user.id)

# Profile Router
profile_router = APIRouter(prefix="/api/py/profile", tags=["profile"])
profile_service = ProfileService()

@profile_router.get("", response_model=Dict[str, Any])
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    profile = profile_service.get_profile(current_user.id)
    if not profile:
        return {"id": current_user.id, "email": current_user.email or ""}
    return profile

@profile_router.put("", response_model=Dict[str, Any])
async def update_profile(profile_data: ProfileUpdate, current_user: CurrentUser = Depends(get_current_user)):
    updated = profile_service.update_profile(current_user.id, profile_data)
    return updated or {"id": current_user.id}

@profile_router.post("/avatar", response_model=Dict[str, Any])
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    try:
        content = await file.read()
        return profile_service.upload_profile_photo(current_user.id, content, file.filename or "avatar.jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Avatar upload failed: {str(e)}")

# Custom Links Router Endpoints
@profile_router.get("/links", response_model=List[Dict[str, Any]])
async def get_custom_links(current_user: CurrentUser = Depends(get_current_user)):
    return profile_service.get_custom_links(current_user.id)

@profile_router.post("/links", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_custom_link(link_data: ProfileLinkCreate, current_user: CurrentUser = Depends(get_current_user)):
    return profile_service.create_custom_link(current_user.id, link_data.name, link_data.url)

@profile_router.put("/links/{link_id}", response_model=Dict[str, Any])
async def update_custom_link(link_id: str, link_data: ProfileLinkUpdate, current_user: CurrentUser = Depends(get_current_user)):
    updated = profile_service.update_custom_link(link_id, current_user.id, link_data.name or "", link_data.url or "")
    if not updated:
        raise HTTPException(status_code=404, detail="Link not found")
    return updated

@profile_router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_link(link_id: str, current_user: CurrentUser = Depends(get_current_user)):
    success = profile_service.delete_custom_link(link_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found")
    return None


