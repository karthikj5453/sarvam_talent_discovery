import os
import time
import logging
from pathlib import Path
from pythonjsonlogger import jsonlogger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import secure

from config import settings
from core.database import engine, Base
from core import models  # noqa — registers all models with SQLAlchemy
from api.routes import auth, candidates, jobs, screening, evaluations, dashboard, analytics, whatsapp

# ─── STRUCTURED JSON LOGGING ──────────────────────────────────
def _setup_logging():
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Remove default handlers, add JSON one
    root.handlers = [handler]

_setup_logging()
logger = logging.getLogger(__name__)

# ─── SENTRY ERROR TRACKING ────────────────────────────────────
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=0.2,          # 20% of requests traced for performance
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
    )
    logger.info("Sentry error tracking initialized", extra={"env": settings.APP_ENV})

# ─── DB INIT ──────────────────────────────────────────────────
# create_all is only used in dev. In production, use: alembic upgrade head
if settings.APP_ENV != "production":
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.warning(f"DB not ready yet, skipping create_all: {e}")

# ─── RATE LIMITER ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# ─── SECURITY HEADERS ─────────────────────────────────────────
secure_headers = secure.Secure(
    server=secure.Server().set(""),                        # hide server header
    hsts=secure.StrictTransportSecurity().max_age(31536000).include_subdomains(),
    xfo=secure.XFrameOptions().deny(),
    xxp=secure.XXSSProtection().set("1; mode=block"),
    content=secure.XContentTypeOptions(),
    csp=secure.ContentSecurityPolicy().default_src("'self'").img_src("*").media_src("*"),
)

app = FastAPI(
    title="Sarvam Talent Discovery Engine",
    description="Multilingual AI-powered hiring platform",
    version="1.1.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,  # hide docs in prod
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── SECURITY HEADERS MIDDLEWARE ──────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    secure_headers.framework.fastapi(response)
    return response

# ─── PERFORMANCE TIMING MIDDLEWARE ────────────────────────────
@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

# ─── LOCAL STATIC FILES (dev audio/resume storage) ────────────
if settings.use_local_storage():
    local_audio_path = Path(settings.LOCAL_STORAGE_PATH)
    local_audio_path.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/static/audio",
        StaticFiles(directory=str(local_audio_path)),
        name="static_audio",
    )
    logger.info(f"Local storage mode: serving files from {local_audio_path.resolve()}")

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
        "version": "1.1.0",
        "storage_mode": "local" if settings.use_local_storage() else "s3",
        "llm_configured": bool(
            settings.GEMINI_API_KEY
            and settings.GEMINI_API_KEY not in ("your_gemini_api_key_here", "")
        ),
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
