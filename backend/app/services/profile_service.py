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

    def resolve_avatar_url(self, raw_url_or_path: str) -> Optional[str]:
        if not raw_url_or_path:
            return raw_url_or_path
        
        # Preserve external URLs (e.g. Google OAuth profile pictures)
        if raw_url_or_path.startswith("http://") or raw_url_or_path.startswith("https://"):
            if "/storage/v1/object/" not in raw_url_or_path and "avatars/" not in raw_url_or_path:
                return raw_url_or_path
            
            # Extract storage object path from legacy stored Supabase URLs
            if "/avatars/" in raw_url_or_path:
                storage_path = raw_url_or_path.split("/avatars/", 1)[1].split("?")[0]
            else:
                return raw_url_or_path
        else:
            storage_path = raw_url_or_path.split("?")[0]
            if storage_path.startswith("avatars/"):
                storage_path = storage_path.replace("avatars/", "", 1)
        
        signed_url = self.repository.get_signed_url("avatars", storage_path)
        if signed_url:
            separator = "&" if "?" in signed_url else "?"
            return f"{signed_url}{separator}v={int(time.time())}"
        return raw_url_or_path

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        profile = self.repository.get_profile(user_id)
        if profile and isinstance(profile, dict):
            raw_photo = profile.get("profile_photo_url")
            if raw_photo:
                profile["profile_photo_url"] = self.resolve_avatar_url(raw_photo)
        return profile

    def update_profile(self, user_id: str, profile_data: ProfileUpdate) -> Optional[Dict[str, Any]]:
        data = profile_data.model_dump(exclude_unset=True)
        updated = self.repository.update_profile(user_id, data)
        if updated and isinstance(updated, dict):
            raw_photo = updated.get("profile_photo_url")
            if raw_photo:
                updated["profile_photo_url"] = self.resolve_avatar_url(raw_photo)
        return updated

    def upload_profile_photo(self, user_id: str, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        ext = filename.split('.')[-1].lower() if '.' in filename else 'jpeg'
        file_path = f"{user_id}/avatar.{ext}"
        content_type = f"image/{ext}" if ext in ["jpeg", "jpg", "png", "webp"] else "image/jpeg"
        
        # Upload file bytes to Supabase Storage
        self.repository.upload_file_to_storage("avatars", file_path, file_bytes, content_type)
        
        # Store ONLY the stable Storage object path in the database record
        updated = self.repository.update_profile(user_id, {"profile_photo_url": file_path})
        
        # Generate a fresh signed URL for the response (without stripping token params)
        fresh_signed_url = self.resolve_avatar_url(file_path)
        
        if updated and isinstance(updated, dict):
            updated["profile_photo_url"] = fresh_signed_url
            return updated
        return {"id": user_id, "profile_photo_url": fresh_signed_url}



