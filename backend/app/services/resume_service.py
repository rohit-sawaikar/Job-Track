import time
from typing import List, Optional, Dict, Any
try:
    from app.repositories.resume_repository import ResumeRepository
    from app.services.resume_parser import ResumeParser
    from app.schemas.resume import ResumeCreate, ResumeUpdate
except ImportError:
    from backend.app.repositories.resume_repository import ResumeRepository
    from backend.app.services.resume_parser import ResumeParser
    from backend.app.schemas.resume import ResumeCreate, ResumeUpdate

class ResumeService:
    def __init__(self):
        self.repository = ResumeRepository()
        self.parser = ResumeParser()

    def get_user_resumes(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            resumes = self.repository.get_user_resumes(user_id)
            if not resumes:
                return []
            
            for r in resumes:
                if not isinstance(r, dict):
                    continue
                name = str(r.get("name") or "")
                if "(" in name and ")" in name:
                    r["resume_type"] = name.rsplit("(", 1)[1].replace(")", "").strip()
                else:
                    r["resume_type"] = r.get("resume_type") or "General"
                
                # Generate signed URLs for private bucket access if file_path is present
                file_path = r.get("file_path")
                if file_path:
                    try:
                        clean_fn = name.replace("/", "_").strip() or "resume"
                        file_ext = r.get("file_type") or "pdf"
                        if not clean_fn.lower().endswith(f".{file_ext}"):
                            clean_fn = f"{clean_fn}.{file_ext}"

                        signed_url = self.repository.get_signed_url("resumes", file_path, download=False)
                        download_url = self.repository.get_signed_url("resumes", file_path, download=True, filename=clean_fn)

                        if signed_url:
                            r["file_url"] = signed_url
                        if download_url:
                            r["download_url"] = download_url
                    except Exception as url_err:
                        pass
            return resumes
        except Exception as e:
            return []

    def get_resume_by_id(self, resume_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            r = self.repository.get_resume_by_id(resume_id, user_id)
            if r and isinstance(r, dict):
                name = str(r.get("name") or "")
                if "(" in name and ")" in name:
                    r["resume_type"] = name.rsplit("(", 1)[1].replace(")", "").strip()
                else:
                    r["resume_type"] = r.get("resume_type") or "General"
                
                file_path = r.get("file_path")
                if file_path:
                    try:
                        clean_fn = name.replace("/", "_").strip() or "resume"
                        file_ext = r.get("file_type") or "pdf"
                        if not clean_fn.lower().endswith(f".{file_ext}"):
                            clean_fn = f"{clean_fn}.{file_ext}"

                        signed_url = self.repository.get_signed_url("resumes", file_path, download=False)
                        download_url = self.repository.get_signed_url("resumes", file_path, download=True, filename=clean_fn)

                        if signed_url:
                            r["file_url"] = signed_url
                        if download_url:
                            r["download_url"] = download_url
                    except Exception:
                        pass
            return r
        except Exception:
            return None

    def create_resume(self, user_id: str, resume_data: ResumeCreate) -> Dict[str, Any]:
        data = resume_data.model_dump()
        resume_type = data.pop('resume_type', 'General')
        if resume_type and resume_type != "General" and f"({resume_type})" not in data.get("name", ""):
            data["name"] = f"{data.get('name', '')} ({resume_type})"
        created = self.repository.create_resume(user_id, data)
        created["resume_type"] = resume_type
        return created

    def upload_resume_file(self, user_id: str, file_bytes: bytes, filename: str, resume_type: str = "General") -> Dict[str, Any]:
        ext = filename.split('.')[-1].lower() if '.' in filename else 'pdf'
        file_path = f"{user_id}/{int(time.time() * 1000)}.{ext}"
        content_type = "application/pdf" if ext == "pdf" else ("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if ext == "docx" else "application/octet-stream")
        
        public_url = self.repository.upload_file_to_storage("resumes", file_path, file_bytes, content_type)
        
        parsed_info = self.parser.parse_resume_content(file_bytes, ext)
        
        existing_resumes = self.repository.get_user_resumes(user_id)
        is_primary = len(existing_resumes) == 0
        
        raw_name = filename.rsplit('.', 1)[0]
        display_name = f"{raw_name} ({resume_type})" if (resume_type and resume_type != "General") else raw_name
        
        clean_fn = raw_name.replace("/", "_").strip() or "resume"
        if not clean_fn.lower().endswith(f".{ext}"):
            clean_fn = f"{clean_fn}.{ext}"

        inline_url = self.repository.get_signed_url("resumes", file_path, download=False)
        download_url = self.repository.get_signed_url("resumes", file_path, download=True, filename=clean_fn)

        resume_data = {
            "name": display_name,
            "file_url": inline_url or public_url,
            "file_path": file_path,
            "file_type": ext,
            "file_size": len(file_bytes),
            "is_primary": is_primary,
            "content_text": parsed_info.get("cleaned_text") or parsed_info.get("raw_text"),
            "skills": parsed_info.get("extracted_skills", []),
            "parsed_data": parsed_info
        }
        created = self.repository.create_resume(user_id, resume_data)
        created["resume_type"] = resume_type
        created["file_url"] = inline_url or public_url
        created["download_url"] = download_url or public_url
        return created


    def set_primary_resume(self, resume_id: str, user_id: str) -> bool:
        return self.repository.set_primary_resume(resume_id, user_id)

    def update_resume(self, resume_id: str, user_id: str, resume_update: ResumeUpdate) -> Dict[str, Any]:
        existing = self.repository.get_resume_by_id(resume_id, user_id)
        if not existing:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Resume not found")
        
        update_data = resume_update.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] is not None:
            clean_name = str(update_data["name"]).strip()
            if not clean_name:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Resume name cannot be empty")
            update_data["name"] = clean_name

        updated = self.repository.update_resume(resume_id, user_id, update_data)
        if not updated:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="Failed to update resume")
        return updated

    def delete_resume(self, resume_id: str, user_id: str) -> bool:
        return self.repository.delete_resume(resume_id, user_id)

    def parse_resume_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        return self.parser.parse_resume_content(file_content, filename)

