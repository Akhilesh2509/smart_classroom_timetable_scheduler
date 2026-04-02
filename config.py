import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Get DB URL from environment
    db_url = os.environ.get("DATABASE_URL")

    # Fix for postgres:// issue (Render/Supabase compatibility)
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Fallback to local DB (for development)
    SQLALCHEMY_DATABASE_URI = db_url or "postgresql://postgres:[YOUR_PASSWORD]@localhost:5432/smart_classroom"

    # Required for Supabase (SSL connection)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"sslmode": "require"}
    }