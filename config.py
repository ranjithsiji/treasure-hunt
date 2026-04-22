import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    """Return the env var value or exit with a clear error."""
    value = os.environ.get(name)
    if not value:
        sys.exit(f"❌  Required environment variable '{name}' is not set. Check your .env file.")
    return value


class Config:
    SECRET_KEY = _require_env('SECRET_KEY')

    # Database connection
    DB_USER     = _require_env('DB_USER')
    DB_PASSWORD = _require_env('DB_PASSWORD')
    DB_HOST     = _require_env('DB_HOST')
    DB_NAME     = _require_env('DB_NAME')
    DB_PORT     = os.environ.get('DB_PORT', '3306')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
