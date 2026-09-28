from pydantic import BaseModel
from typing import Optional, List

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_level: Optional[str] = None
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    work_preference: Optional[str] = None
    career_interests: Optional[str] = None
    is_profile_complete: Optional[bool] = None

class ProfileResponse(BaseModel):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_level: Optional[str] = "Mid Level"
    preferred_roles: Optional[List[str]] = []
    preferred_locations: Optional[List[str]] = []
    work_preference: Optional[str] = "Remote"
    career_interests: Optional[str] = None
    is_profile_complete: bool = False
    created_at: Optional[str] = None
