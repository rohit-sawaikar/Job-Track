try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

from typing import Optional
from supabase import create_client, Client
import logging


logger = logging.getLogger(__name__)

_supabase_client_instance: Optional[Client] = None

def get_supabase_client() -> Client:
    global _supabase_client_instance
    if _supabase_client_instance is None:
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        _supabase_client_instance = create_client(url, key)
    return _supabase_client_instance

class BaseRepository:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        self._client = None

    @property
    def client(self) -> Client:
        return get_supabase_client()


    def upload_file_to_storage(self, bucket_name: str, file_path: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Uploads file bytes to Supabase storage bucket directly.
        If the bucket does not exist, lazy-creates a private bucket and retries the upload.
        Returns a signed URL or path reference for the stored object.
        """
        try:
            try:
                self.client.storage.from_(bucket_name).upload(
                    file_path,
                    file_bytes,
                    file_options={"content-type": content_type, "upsert": "true"}
                )
            except Exception as upload_err:
                err_msg = str(upload_err).lower()
                if "bucket" in err_msg or "not found" in err_msg or "404" in err_msg:
                    logger.info(f"Bucket '{bucket_name}' not found. Creating private bucket...")
                    try:
                        self.client.storage.create_bucket(bucket_name, options={"public": False})
                    except Exception as b_err:
                        logger.warning(f"Could not create bucket '{bucket_name}': {b_err}")
                    
                    # Retry upload
                    self.client.storage.from_(bucket_name).upload(
                        file_path,
                        file_bytes,
                        file_options={"content-type": content_type, "upsert": "true"}
                    )
                else:
                    raise upload_err

            return self.get_signed_url(bucket_name, file_path)
        except Exception as e:
            logger.error(f"Error uploading file to storage bucket {bucket_name}: {e}")
            return f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"

    def get_signed_url(self, bucket_name: str, file_path: str, expires_in: int = 3600) -> str:
        """Generates a temporary signed URL for private bucket file viewing/downloading."""
        try:
            res = self.client.storage.from_(bucket_name).create_signed_url(file_path, expires_in)
            if isinstance(res, dict) and "signedUrl" in res:
                return res["signedUrl"]
            elif isinstance(res, str):
                return res
            elif hasattr(res, "get"):
                return res.get("signedUrl", f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}")
            return f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
        except Exception as e:
            logger.warning(f"Signed URL creation fallback for {bucket_name}/{file_path}: {e}")
            return f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"

    def download_file_from_storage(self, bucket_name: str, file_path: str) -> Optional[bytes]:
        """Downloads file bytes directly from Supabase Storage bucket."""
        try:
            return self.client.storage.from_(bucket_name).download(file_path)
        except Exception as e:
            logger.error(f"Error downloading file from storage bucket {bucket_name}/{file_path}: {e}")
            return None



