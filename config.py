import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    db_url = os.environ.get("DATABASE_URL")

    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Fallback for local
    SQLALCHEMY_DATABASE_URI = db_url or "postgresql://postgres:YOUR_PASSWORD@localhost:5432/smart_classroom"

    # ✅ Apply SSL only for Supabase / production
    if db_url:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {"sslmode": "require"}
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}