import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    APP_TITLE: str = os.getenv("APP_TITLE", "Kitchen & Plant Maintenance CMMS Analytics")
    USE_MOCK_DATA: bool = os.getenv("USE_MOCK_DATA", "false").lower() in ("true", "1", "yes")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DEFAULT_DATE_RANGE_DAYS: int = int(os.getenv("DEFAULT_DATE_RANGE_DAYS", "30"))
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1")

settings = Settings()
