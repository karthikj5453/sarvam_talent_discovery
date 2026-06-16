from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ─── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/sarvam_talent"

    # ─── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ─── Sarvam AI ────────────────────────────────────────────────
    SARVAM_API_KEY: str = ""
    SARVAM_BASE_URL: str = "https://api.sarvam.ai"

    # ─── JWT ──────────────────────────────────────────────────────
    SECRET_KEY: str = "change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ─── AWS S3 ───────────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = "sarvam-talent-audio"
    AWS_REGION: str = "ap-south-1"

    # ─── App ──────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
