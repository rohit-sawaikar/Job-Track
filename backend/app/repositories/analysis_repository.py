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

    # Custom Links (profile_links table with fallback to custom_links column in profiles table)
    def get_custom_links(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.client.from_('profile_links').select('*').eq('user_id', user_id).order('created_at').execute()
            if res.data is not None:
                return res.data
        except Exception as e:
            logger.warning(f"Could not fetch from profile_links: {e}")
        
        try:
            p = self.get_profile(user_id)
            if p and isinstance(p, dict):
                return p.get("custom_links") or []
        except Exception:
            pass
        return []

    def create_custom_link(self, user_id: str, name: str, url: str) -> Dict[str, Any]:
        payload = {"user_id": user_id, "name": name, "url": url}
        try:
            res = self.client.from_('profile_links').insert(payload).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.warning(f"Could not insert into profile_links: {e}")
        
        import uuid
        new_link = {"id": str(uuid.uuid4()), "user_id": user_id, "name": name, "url": url}
        existing = self.get_custom_links(user_id)
        existing.append(new_link)
        self.update_profile(user_id, {"custom_links": existing})
        return new_link

    def update_custom_link(self, link_id: str, user_id: str, name: str, url: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.from_('profile_links').update({"name": name, "url": url}).eq('id', link_id).eq('user_id', user_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.warning(f"Could not update profile_links: {e}")
        
        existing = self.get_custom_links(user_id)
        updated_link = None
        for link in existing:
            if str(link.get("id")) == str(link_id):
                link["name"] = name
                link["url"] = url
                updated_link = link
                break
        if updated_link:
            self.update_profile(user_id, {"custom_links": existing})
            return updated_link
        return None

    def delete_custom_link(self, link_id: str, user_id: str) -> bool:
        try:
            res = self.client.from_('profile_links').delete().eq('id', link_id).eq('user_id', user_id).execute()
            if res.data:
                return True
        except Exception as e:
            logger.warning(f"Could not delete from profile_links: {e}")
        
        existing = self.get_custom_links(user_id)
        filtered = [l for l in existing if str(l.get("id")) != str(link_id)]
        if len(filtered) != len(existing):
            self.update_profile(user_id, {"custom_links": filtered})
            return True
        return False

