from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from core.database import engine, Base

# Import all models so SQLAlchemy knows about them
from core import models  # noqa

# Import routers
from api.routes import auth, candidates, jobs, screening, evaluations, dashboard, analytics

# Create all tables on startup
Base.metadata.create_all(bind=engine)

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

# ─── ROUTES ───────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
app.include_router(candidates.router,   prefix="/candidates",   tags=["Candidates"])
app.include_router(jobs.router,         prefix="/jobs",         tags=["Jobs"])
app.include_router(screening.router,    prefix="/screening",    tags=["Screening"])
app.include_router(evaluations.router,  prefix="/evaluations",  tags=["Evaluations"])
app.include_router(dashboard.router,    prefix="/dashboard",    tags=["Dashboard"])
app.include_router(analytics.router,    prefix="/analytics",    tags=["Analytics"])


# ─── HEALTH CHECK ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Sarvam Talent Discovery API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}