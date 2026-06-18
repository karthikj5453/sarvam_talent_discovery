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

    # ─── Gemini LLM (for competency scoring + question generation) ─
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ─── JWT ──────────────────────────────────────────────────────
    SECRET_KEY: str = "change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ─── AWS S3 ───────────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = "sarvam-talent-audio"
    AWS_REGION: str = "ap-south-1"

    # ─── Storage ──────────────────────────────────────────────────
    # Set LOCAL_STORAGE_PATH to use local disk instead of S3 in dev.
    # If AWS creds are empty/placeholder, local storage is used automatically.
    LOCAL_STORAGE_PATH: str = "./local_audio"

    # ─── Evaluation mode ──────────────────────────────────────────
    # ASYNC_EVAL=true  → fire Celery task (requires Redis + worker)
    # ASYNC_EVAL=false → run evaluation inline/synchronously (dev mode)
    ASYNC_EVAL: bool = False

    # ─── App ──────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]

    # ─── SMTP Email Notifications ─────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@sarvam.ai"

    def use_local_storage(self) -> bool:
        """Returns True if AWS creds are absent/placeholder — use local disk storage."""
        placeholder = {"your_aws_key", "your_aws_secret", "", "your_key", "your_secret"}
        return (
            self.AWS_ACCESS_KEY_ID in placeholder
            or self.AWS_SECRET_ACCESS_KEY in placeholder
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
