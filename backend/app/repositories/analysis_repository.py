import logging
from typing import List, Optional, Dict, Any
try:
    from app.repositories.base_repository import BaseRepository
except ImportError:
    from backend.app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

ALLOWED_ANALYSIS_COLUMNS = {
    'id', 'user_id', 'job_id', 'resume_id', 'match_score', 'job_title', 'company', 'short_summary', 'created_at'
}


class AnalysisRepository(BaseRepository):
    def save_analysis(self, user_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis_data['user_id'] = user_id
        db_payload = {k: v for k, v in analysis_data.items() if k in ALLOWED_ANALYSIS_COLUMNS}
        try:
            res = self.client.from_('resume_analyses').insert(db_payload).execute()
            return res.data[0] if res.data else db_payload
        except Exception as e:
            logger.error(f"Failed to persist resume analysis for user {user_id}: {e}")
            return analysis_data

    def get_user_analyses(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            res = self.client.from_('resume_analyses').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Failed to fetch analyses for user {user_id}: {e}")
            return []


class ProfileRepository(BaseRepository):
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        res = self.client.from_('profiles').select('*').eq('id', user_id).single().execute()
        return res.data

    def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        res = self.client.from_('profiles').update(profile_data).eq('id', user_id).execute()
        return res.data[0] if res.data else None
