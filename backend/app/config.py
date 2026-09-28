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
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    NEXT_PUBLIC_SUPABASE_URL: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    SUPABASE_ANON_KEY: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()

