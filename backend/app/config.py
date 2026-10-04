import os
from pathlib import Path
from dotenv import load_dotenv

# Try loading .env.local first, then .env
root_dir = Path(__file__).resolve().parent.parent.parent
env_local = root_dir / ".env.local"
env_file = root_dir / ".env"

if env_local.exists():
    load_dotenv(dotenv_path=env_local)
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
load_dotenv()  # Fallback to current working directory

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    NEXT_PUBLIC_SUPABASE_URL: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or 
        os.getenv("SUPABASE_SERVICE_KEY", "").strip() or 
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
    )
    SUPABASE_ANON_KEY: str = (
        os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "").strip() or 
        os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "").strip()
    PORT: int = int(os.getenv("PORT", "8000"))

    @classmethod
    def get_supabase_credential_info(cls) -> dict:
        """Returns safe diagnostic info regarding which Supabase server key source was selected."""
        sources = ["SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY", "SUPABASE_SECRET_KEY"]
        selected_source = None
        key_val = ""
        for s in sources:
            val = os.getenv(s, "").strip()
            if val:
                selected_source = s
                key_val = val
                break
        
        if not selected_source:
            anon_val = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "").strip() or os.getenv("SUPABASE_ANON_KEY", "").strip()
            return {
                "selected_source": "NONE (Falling back to anon key)",
                "present": bool(anon_val),
                "is_service_secret": False
            }
        
        # Check if the selected key is likely a service-role secret vs publishable key
        is_service_secret = not (key_val.startswith("sbp_") or "anon" in selected_source.lower())
        return {
            "selected_source": selected_source,
            "present": True,
            "is_service_secret": is_service_secret
        }

settings = Settings()

