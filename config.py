import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Default settings. Override with environment variables (or a .env file)."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-key-please-change-in-production")
    DATABASE_PATH: str = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "database", "library.db")
    )
    TOKEN_EXPIRATION: int = int(os.environ.get("TOKEN_EXPIRATION", "3600"))
    PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
