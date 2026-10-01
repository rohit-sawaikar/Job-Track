from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response, Cookie, Header, Request
from typing import List, Dict, Any, Optional
import time
import os
import jwt

try:
    from app.api.deps import get_current_user, CurrentUser, validate_uuid
    from app.config import settings
    from app.schemas.resume import ResumeCreate, ResumeUpdate
    from app.schemas.analysis import AnalysisCreateRequest
    from app.schemas.profile import ProfileUpdate, ProfileLinkCreate, ProfileLinkUpdate
    from app.services.resume_service import ResumeService
    from app.services.analysis_service import AnalysisService
    from app.services.profile_service import ProfileService
except ImportError:
    from backend.app.api.deps import get_current_user, CurrentUser, validate_uuid
    from backend.app.config import settings
    from backend.app.schemas.resume import ResumeCreate, ResumeUpdate
    from backend.app.schemas.analysis import AnalysisCreateRequest
    from backend.app.schemas.profile import ProfileUpdate, ProfileLinkCreate, ProfileLinkUpdate
    from backend.app.services.resume_service import ResumeService
    from backend.app.services.analysis_service import AnalysisService
    from backend.app.services.profile_service import ProfileService

# Resumes Router
resumes_router = APIRouter(prefix="/api/py/resumes", tags=["resumes"])
resume_service = ResumeService()

PREVIEW_COOKIE_NAME = "jt_resume_preview"
PREVIEW_COOKIE_MAX_AGE = 60

def _get_preview_secret() -> str:
    return (getattr(settings, "SUPABASE_JWT_SECRET", "") or 
            getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "") or 
            "jt_preview_secret_key_2026").strip()

def generate_preview_token(user_id: str, resume_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "resume_id": resume_id,
        "type": "resume_preview",
        "iat": now,
        "exp": now + PREVIEW_COOKIE_MAX_AGE
    }
    return jwt.encode(payload, _get_preview_secret(), algorithm="HS256")

def verify_preview_cookie(cookie_val: Optional[str], expected_resume_id: str) -> str:
    if not cookie_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing preview session cookie"
        )
    try:
        payload = jwt.decode(cookie_val, _get_preview_secret(), algorithms=["HS256"])
        if payload.get("type") != "resume_preview":
            raise ValueError("Invalid preview token type")
        if payload.get("resume_id") != expected_resume_id:
            raise ValueError("Preview token resume_id mismatch")
        user_id = payload.get("sub")
        if not user_id or not validate_uuid(user_id):
            raise ValueError("Invalid user_id in preview token")
        return str(user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired preview session: {str(e)}"
        )

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

@resumes_router.post("/{resume_id}/preview-session")
async def create_preview_session(
    resume_id: str,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user)
):
    print(f"[Resume Preview] authenticated user: {current_user.id}")
    resume = resume_service.get_resume_by_id(resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    print("[Resume Preview] resume ownership verified")

    token = generate_preview_token(current_user.id, resume_id)
    print("[Resume Preview] preview credential valid")

    is_secure = os.getenv("VERCEL_ENV") == "production" or os.getenv("NODE_ENV") == "production"
    response.set_cookie(
        key=PREVIEW_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=PREVIEW_COOKIE_MAX_AGE,
        path="/api/py/resumes",
    )
    print("[Resume Preview] preview session status: 200")
    return {"success": True}

@resumes_router.get("/{resume_id}/view")
async def view_resume(
    resume_id: str,
    request: Request,
    jt_resume_preview: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    cookie_header = request.headers.get("cookie")
    cookie_names = []
    if cookie_header:
        for part in cookie_header.split(";"):
            name = part.split("=", 1)[0].strip()
            if name:
                cookie_names.append(name)

    print("[Resume View Diagnostic] path:", request.url.path)
    print("[Resume View Diagnostic] host:", request.headers.get("host"))
    print("[Resume View Diagnostic] origin:", request.headers.get("origin"))
    print("[Resume View Diagnostic] has_cookie_header:", bool(cookie_header))
    print("[Resume View Diagnostic] cookie_names:", cookie_names)
    print("[Resume View Diagnostic] has_preview_cookie:", "jt_resume_preview" in request.cookies)

    print("[Resume Preview] opening PDF endpoint")
    user_id = None
    if jt_resume_preview:
        user_id = verify_preview_cookie(jt_resume_preview, resume_id)
        print(f"[Resume Preview] authenticated user: {user_id}")
    elif authorization:
        user = await get_current_user(authorization=authorization)
        user_id = user.id
        print(f"[Resume Preview] authenticated user (Authorization header): {user_id}")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing preview session cookie or Authorization header"
        )

    resume = resume_service.get_resume_by_id(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    print("[Resume Preview] resume ownership verified")

    file_path = resume.get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="Resume file path missing")
    
    file_bytes = resume_service.repository.download_file_from_storage("resumes", file_path)
    if not file_bytes:
        url = resume.get("file_url")
        if not url:
            raise HTTPException(status_code=404, detail="Resume view URL unavailable")
        return {"url": url, "file_type": resume.get("file_type", "pdf"), "name": resume.get("name", "")}

    file_type = (resume.get("file_type") or "pdf").lower()
    media_type = "application/pdf" if file_type == "pdf" else ("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if file_type == "docx" else "application/octet-stream")
    
    raw_name = resume.get("name") or "resume"
    clean_fn = raw_name.replace("/", "_").strip()
    if not clean_fn.lower().endswith(f".{file_type}"):
        clean_fn = f"{clean_fn}.{file_type}"

    headers = {
        "Content-Disposition": f"inline; filename=\"{clean_fn}\"",
        "Content-Type": media_type,
    }
    print("[Resume Preview Headers] content_type:", media_type)
    print("[Resume Preview Headers] content_disposition:", headers.get("Content-Disposition"))
    print("[Resume Preview Headers] content_length:", len(file_bytes) if file_bytes else 0)
    print("[Resume Preview Headers] filename:", clean_fn)
    print("[Resume Preview] PDF response status: 200")
    return Response(content=file_bytes, media_type=media_type, headers=headers)

@resumes_router.get("/{resume_id}/download")
async def download_resume(resume_id: str, current_user: CurrentUser = Depends(get_current_user)):
    resume = resume_service.get_resume_by_id(resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    file_path = resume.get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="Resume file path missing")
    
    file_bytes = resume_service.repository.download_file_from_storage("resumes", file_path)
    if not file_bytes:
        url = resume.get("download_url") or resume.get("file_url")
        if not url:
            raise HTTPException(status_code=404, detail="Resume download URL unavailable")
        return {"url": url, "file_type": resume.get("file_type", "pdf"), "name": resume.get("name", "")}

    file_type = (resume.get("file_type") or "pdf").lower()
    media_type = "application/pdf" if file_type == "pdf" else ("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if file_type == "docx" else "application/octet-stream")
    
    raw_name = resume.get("name") or "resume"
    clean_fn = raw_name.replace("/", "_").strip()
    if not clean_fn.lower().endswith(f".{file_type}"):
        clean_fn = f"{clean_fn}.{file_type}"

    headers = {
        "Content-Disposition": f"attachment; filename=\"{clean_fn}\"",
        "Content-Type": media_type,
    }
    return Response(content=file_bytes, media_type=media_type, headers=headers)

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
@profile_router.post("", response_model=Dict[str, Any])
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


