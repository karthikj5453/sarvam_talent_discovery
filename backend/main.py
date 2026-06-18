import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import settings
from core.database import engine, Base

# Import all models so SQLAlchemy knows about them
from core import models  # noqa

# Import routers
from api.routes import auth, candidates, jobs, screening, evaluations, dashboard, analytics, whatsapp

# Create all tables on startup (best-effort — won't crash if DB is unreachable)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[WARNING] DB not ready yet, skipping create_all: {e}")

app = FastAPI(
    title="Sarvam Talent Discovery Engine",
    description="Multilingual AI-powered hiring platform",
    version="1.0.0",
)

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── LOCAL STATIC FILES (dev audio/resume storage) ────────────
# When AWS creds are absent, audio and resume files are stored on disk.
# This mounts the local_audio directory so the frontend can play them back.
if settings.use_local_storage():
    local_audio_path = Path(settings.LOCAL_STORAGE_PATH)
    local_audio_path.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/static/audio",
        StaticFiles(directory=str(local_audio_path)),
        name="static_audio",
    )
    print(f"[INFO] Local storage mode: serving files from {local_audio_path.resolve()}")

# ─── ROUTES ───────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
app.include_router(candidates.router,   prefix="/candidates",   tags=["Candidates"])
app.include_router(jobs.router,         prefix="/jobs",         tags=["Jobs"])
app.include_router(screening.router,    prefix="/screening",    tags=["Screening"])
app.include_router(evaluations.router,  prefix="/evaluations",  tags=["Evaluations"])
app.include_router(dashboard.router,    prefix="/dashboard",    tags=["Dashboard"])
app.include_router(analytics.router,    prefix="/analytics",    tags=["Analytics"])
app.include_router(whatsapp.router,     prefix="/whatsapp",     tags=["WhatsApp"])


# ─── HEALTH CHECK ─────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Sarvam Talent Discovery API is running",
        "storage_mode": "local" if settings.use_local_storage() else "s3",
        "llm_configured": bool(
            settings.GEMINI_API_KEY
            and settings.GEMINI_API_KEY not in ("your_gemini_api_key_here", "")
        ),
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
