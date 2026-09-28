from pydantic import BaseModel
from typing import Optional

class ResumeBase(BaseModel):
    name: str
    resume_type: Optional[str] = "General"

class ResumeCreate(ResumeBase):
    file_url: str
    file_path: str
    file_type: str
    file_size: int
    is_primary: Optional[bool] = False

class ResumeUpdate(BaseModel):
    name: Optional[str] = None
    resume_type: Optional[str] = None
    is_primary: Optional[bool] = None

class ResumeResponse(ResumeBase):
    id: str
    user_id: str
    file_url: str
    file_path: str
    file_type: str
    file_size: int
    is_primary: bool
    created_at: str
    updated_at: str
