from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class JobBase(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = "Remote"
    salary: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    experience: Optional[str] = None
    employment_type: Optional[str] = "Full-time"
    job_url: Optional[str] = None
    application_url: Optional[str] = None
    application_date: Optional[str] = None
    status: str = "saved"
    notes: Optional[str] = None
    is_favorite: Optional[bool] = False

class JobCreate(JobBase):
    raw_job_text: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience: Optional[str] = None
    employment_type: Optional[str] = None
    job_url: Optional[str] = None
    application_url: Optional[str] = None
    application_date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None

class JobResponse(JobBase):
    id: str
    user_id: str
    created_at: str
    updated_at: str
