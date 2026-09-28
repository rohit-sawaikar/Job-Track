from app.repositories.job_repository import JobRepository
from app.services.job_extractor import JobExtractor
from app.schemas.job import JobCreate, JobUpdate
from typing import List, Optional, Dict, Any

class JobService:
    def __init__(self):
        self.repository = JobRepository()
        self.extractor = JobExtractor()

    def get_user_jobs(self, user_id: str) -> List[Dict[str, Any]]:
        return self.repository.get_user_jobs(user_id)

    def get_job_by_id(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self.repository.get_job_by_id(job_id, user_id)

    def create_job(self, user_id: str, job_data: JobCreate) -> Dict[str, Any]:
        data = job_data.model_dump(exclude_unset=True)
        raw_text = data.pop('raw_job_text', None)

        # Merge preferred_skills into skills
        pref_skills = data.pop('preferred_skills', []) or []
        req_skills = data.get('skills', []) or []
        combined_skills = []
        for s in (req_skills + pref_skills):
            if s and s not in combined_skills:
                combined_skills.append(s)
        data['skills'] = combined_skills

        # Map work_mode into location if present
        work_mode = data.pop('work_mode', None)
        if work_mode and work_mode.strip():
            loc = data.get('location')
            if loc and work_mode.lower() not in loc.lower():
                data['location'] = f"{loc} ({work_mode})"
            elif not loc:
                data['location'] = work_mode

        # If raw text provided and skills/description empty, extract with AI
        if raw_text and not data.get('description'):
            extracted = self.extractor.extract_job_details(raw_text)
            data['title'] = data.get('title') or extracted.get('title') or 'Target Position'
            data['company'] = data.get('company') or extracted.get('company')
            data['location'] = data.get('location') or extracted.get('location')
            data['description'] = raw_text
            data['requirements'] = extracted.get('requirements')
            data['skills'] = extracted.get('required_skills') or []
            data['salary'] = data.get('salary') or extracted.get('salary')

        return self.repository.create_job(user_id, data)

    def update_job(self, job_id: str, user_id: str, job_data: JobUpdate) -> Optional[Dict[str, Any]]:
        data = job_data.model_dump(exclude_unset=True)

        if 'preferred_skills' in data:
            pref_skills = data.pop('preferred_skills', []) or []
            req_skills = data.get('skills', []) or []
            combined_skills = []
            for s in (req_skills + pref_skills):
                if s and s not in combined_skills:
                    combined_skills.append(s)
            data['skills'] = combined_skills

        if 'work_mode' in data:
            work_mode = data.pop('work_mode', None)
            if work_mode and work_mode.strip():
                loc = data.get('location')
                if loc and work_mode.lower() not in loc.lower():
                    data['location'] = f"{loc} ({work_mode})"
                elif not loc:
                    data['location'] = work_mode

        return self.repository.update_job(job_id, user_id, data)


    def delete_job(self, job_id: str, user_id: str) -> bool:
        return self.repository.delete_job(job_id, user_id)
