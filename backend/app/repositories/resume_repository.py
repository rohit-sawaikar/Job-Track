import logging
from app.repositories.base_repository import BaseRepository
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

ALLOWED_RESUME_COLUMNS = {
    'id', 'user_id', 'name', 'file_path', 'file_url', 'file_size', 'file_type', 'is_primary', 'created_at', 'updated_at',
    'content_text', 'skills', 'parsed_data'
}

class ResumeRepository(BaseRepository):
    def get_user_resumes(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.client.from_('resumes').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching resumes for user {user_id}: {e}")
            return []

    def get_resume_by_id(self, resume_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            query = self.client.from_('resumes').select('*').eq('id', resume_id)
            if user_id:
                query = query.eq('user_id', user_id)
            res = query.single().execute()
            return res.data
        except Exception as e:
            logger.error(f"Error fetching resume {resume_id}: {e}")
            return None

    def create_resume(self, user_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        resume_data['user_id'] = user_id
        db_payload = {k: v for k, v in resume_data.items() if k in ALLOWED_RESUME_COLUMNS}
        try:
            res = self.client.from_('resumes').insert(db_payload).execute()
            return res.data[0] if res.data else db_payload
        except Exception as e:
            logger.error(f"Error creating resume for user {user_id}: {e}")
            raise e

    def set_primary_resume(self, resume_id: str, user_id: str) -> bool:
        try:
            # Clear primary for user
            self.client.from_('resumes').update({'is_primary': False}).eq('user_id', user_id).execute()
            # Set primary for target resume
            self.client.from_('resumes').update({'is_primary': True}).eq('id', resume_id).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error setting primary resume {resume_id} for user {user_id}: {e}")
            return False

    def delete_resume(self, resume_id: str, user_id: str) -> bool:
        try:
            self.client.from_('resumes').delete().eq('id', resume_id).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting resume {resume_id} for user {user_id}: {e}")
            return False


