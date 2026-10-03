import logging
import re
from app.repositories.base_repository import BaseRepository
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

ALLOWED_JOB_COLUMNS = {
    'id', 'user_id', 'title', 'company', 'location', 'status', 'salary',
    'description', 'requirements', 'skills', 'experience', 'employment_type',
    'job_url', 'application_url', 'application_date', 'notes', 'is_favorite',
    'created_at', 'updated_at'
}

class JobRepository(BaseRepository):
    def get_user_jobs(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.client.from_('jobs').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching jobs for user {user_id}: {e}")
            return []

    def get_job_by_id(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.from_('jobs').select('*').eq('id', job_id).eq('user_id', user_id).single().execute()
            return res.data
        except Exception as e:
            logger.error(f"Error fetching job {job_id} for user {user_id}: {e}")
            return None

    def create_job(self, user_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        job_data['user_id'] = user_id
        db_payload = {k: v for k, v in job_data.items() if k in ALLOWED_JOB_COLUMNS}
        try:
            res = self.client.from_('jobs').insert(db_payload).execute()
            data = res.data[0] if res.data else db_payload
            
            # Insert activity record safely
            try:
                self.client.from_('job_activities').insert({
                    'job_id': data.get('id'),
                    'user_id': user_id,
                    'event_type': 'created',
                    'description': f"Job '{data.get('title')}' created via Python Backend API",
                }).execute()
            except Exception as act_err:
                logger.warning(f"Failed to log job activity: {act_err}")
            
            return data
        except Exception as e:
            logger.error(f"Error creating job for user {user_id}: {e}")
            raise e

    def update_job(self, job_id: str, user_id: str, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        db_payload = {k: v for k, v in job_data.items() if k in ALLOWED_JOB_COLUMNS}
        try:
            res = self.client.from_('jobs').update(db_payload).eq('id', job_id).eq('user_id', user_id).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error updating job {job_id} for user {user_id}: {e}")
            return None

    def delete_job(self, job_id: str, user_id: str) -> bool:
        try:
            res = self.client.from_('jobs').delete().eq('id', job_id).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting job {job_id} for user {user_id}: {e}")
            return False

    def check_duplicate_job(self, user_id: str, title: str, company: Optional[str] = None, job_url: Optional[str] = None, application_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Check for duplicate jobs for a user using normalized title, company, and URLs.
        """
        jobs = self.get_user_jobs(user_id)
        if not jobs:
            return {"is_duplicate": False, "existing_job": None}

        norm_title = (title or "").strip().lower()
        norm_company = (company or "").strip().lower()

        clean_urls = []
        for u in [job_url, application_url]:
            if u and isinstance(u, str) and u.strip():
                c_u = u.strip().lower().rstrip('/')
                c_u = re.sub(r'^https?://', '', c_u)
                if c_u:
                    clean_urls.append(c_u)

        for j in jobs:
            j_title = (j.get("title") or "").strip().lower()
            j_company = (j.get("company") or "").strip().lower()

            # Check URL match
            j_urls = []
            for u in [j.get("job_url"), j.get("application_url")]:
                if u and isinstance(u, str) and u.strip():
                    c_u = u.strip().lower().rstrip('/')
                    c_u = re.sub(r'^https?://', '', c_u)
                    if c_u:
                        j_urls.append(c_u)

            url_matched = any(u in j_urls for u in clean_urls) if clean_urls and j_urls else False

            # Check title & company match
            title_matched = (norm_title == j_title)
            company_matched = False
            if norm_company and j_company:
                company_matched = (norm_company == j_company)
            elif not norm_company and not j_company:
                company_matched = True

            if url_matched or (title_matched and company_matched):
                return {
                    "is_duplicate": True,
                    "existing_job": {
                        "id": j.get("id"),
                        "title": j.get("title"),
                        "company": j.get("company"),
                        "created_at": j.get("created_at"),
                        "status": j.get("status")
                    }
                }

        return {"is_duplicate": False, "existing_job": None}


