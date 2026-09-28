import time
from typing import Optional, Dict, Any
try:
    from app.repositories.analysis_repository import ProfileRepository
    from app.schemas.profile import ProfileUpdate
except ImportError:
    from backend.app.repositories.analysis_repository import ProfileRepository
    from backend.app.schemas.profile import ProfileUpdate

class ProfileService:
    def __init__(self):
        self.repository = ProfileRepository()

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.repository.get_profile(user_id)

    def update_profile(self, user_id: str, profile_data: ProfileUpdate) -> Optional[Dict[str, Any]]:
        data = profile_data.model_dump(exclude_unset=True)
        return self.repository.update_profile(user_id, data)

    def upload_profile_photo(self, user_id: str, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        ext = filename.split('.')[-1].lower() if '.' in filename else 'jpeg'
        file_path = f"{user_id}/avatar.{ext}"
        content_type = f"image/{ext}" if ext in ["jpeg", "jpg", "png", "webp"] else "image/jpeg"
        
        public_url = self.repository.upload_file_to_storage("avatars", file_path, file_bytes, content_type)
        base_url = public_url.split('?')[0] if public_url else ""
        cache_busted_url = f"{base_url}?v={int(time.time())}" if base_url else public_url
        
        updated = self.repository.update_profile(user_id, {"profile_photo_url": cache_busted_url})
        return updated or {"id": user_id, "profile_photo_url": cache_busted_url}


