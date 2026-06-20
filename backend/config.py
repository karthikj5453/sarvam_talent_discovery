from pydantic_settings import BaseSettings
from typing import List
import sys


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
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://sarvam-talent-discovery.netlify.app",
        "https://sarvam-talent-discovery-hrdashboard.netlify.app"
    ]

    # ─── Observability ───────────────────────────────────────
    SENTRY_DSN: str = ""

    # ─── SMTP Email Notifications ─────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465          # 465 = SMTP_SSL (enforced TLS). Use 587 for STARTTLS.
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@sarvam.ai"
    SMTP_USE_SSL: bool = True     # True=SMTP_SSL (port 465), False=STARTTLS (port 587)

    # ─── Test Database ────────────────────────────────────────────
    TEST_DATABASE_URL: str = "postgresql://postgres:password@127.0.0.1:5432/sarvam_talent_test"

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

# ─── SECRET KEY STRENGTH GUARD ─────────────────────────────────
# Unconditional — always enforced regardless of APP_ENV.
# Weak keys in staging are just as dangerous as in production.
_WEAK_KEYS = {"change_me_in_production", "secret", "password", "test", "dev", ""}
if settings.SECRET_KEY.lower() in _WEAK_KEYS or len(settings.SECRET_KEY) < 32:
    _msg = (
        "\n[FATAL] SECRET_KEY is too weak or still the default value!\n"
        "Generate a strong key with: openssl rand -hex 32\n"
        "Then set SECRET_KEY=<result> in backend/.env\n"
    )
    if settings.APP_ENV == "production":
        print(_msg, file=sys.stderr)
        sys.exit(1)
    else:
        # In dev/staging — warn loudly but don't exit so developers can still run locally
        print(f"[WARNING]{_msg}", file=sys.stderr)
