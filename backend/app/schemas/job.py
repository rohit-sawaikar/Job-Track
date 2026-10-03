from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

ALLOWED_STATUSES = {"saved", "applied", "screening", "interview", "offer", "rejected", "withdrawn"}

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

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Job title cannot be empty or whitespace-only.")
        return v.strip()

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if v is None:
            return "saved"
        norm = str(v).strip().lower()
        if norm not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values: {', '.join(sorted(ALLOWED_STATUSES))}")
        return norm

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 50000:
            raise ValueError("Job description text exceeds maximum allowed length of 50,000 characters.")
        return v

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

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Job title cannot be empty or whitespace-only.")
        return v.strip() if v is not None else None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        norm = str(v).strip().lower()
        if norm not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values: {', '.join(sorted(ALLOWED_STATUSES))}")
        return norm

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 50000:
            raise ValueError("Job description text exceeds maximum allowed length of 50,000 characters.")
        return v

class JobDuplicateCheckRequest(BaseModel):
    title: str
    company: Optional[str] = None
    job_url: Optional[str] = None
    application_url: Optional[str] = None

class JobResponse(JobBase):
    id: str
    user_id: str
    created_at: str
    updated_at: str

