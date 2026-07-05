import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Database ──────────────────────────────────────────────────────────────────
# Defaults to SQLite for local development. Set DATABASE_URL in .env for Postgres.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'datainsight.db')}"
)

# ── Supabase (Storage + Auth verification) ────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # legacy alias
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
# Use the most specific key available for storage and auth.
SUPABASE_STORAGE_KEY = SUPABASE_ANON_KEY or SUPABASE_KEY or SUPABASE_SERVICE_ROLE_KEY
SUPABASE_AUTH_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
# Storage bucket name inside Supabase Storage
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "datainsight-csv")

# ── Local fallback storage (used when Supabase is not configured) ─────────────
STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(BASE_DIR, "storage"))
os.makedirs(STORAGE_DIR, exist_ok=True)

# Use Supabase Storage when both URL and a storage key are defined
USE_CLOUD_STORAGE = bool(SUPABASE_URL and SUPABASE_STORAGE_KEY)
# Enable Supabase Auth validation when a service role key is provided
USE_SUPABASE_AUTH = bool(SUPABASE_URL and SUPABASE_AUTH_KEY)

# ── AI API Keys ───────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.4"))

# ── Upload constraints ────────────────────────────────────────────────────────
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {".csv"}

# ── CORS ──────────────────────────────────────────────────────────────────────
# Space-separated list of allowed origins. Defaults to '*' for dev mode.
# Example prod value: "https://datainsight.vercel.app https://www.mydomain.com"
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = (
    ["*"] if ALLOWED_ORIGINS_RAW.strip() == "*"
    else [o.strip() for o in ALLOWED_ORIGINS_RAW.split() if o.strip()]
)
