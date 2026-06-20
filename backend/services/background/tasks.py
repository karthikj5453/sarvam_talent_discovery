"""
Celery Background Task Worker

Runs the AI evaluation pipeline asynchronously so the HTTP response
returns immediately when a screening session is completed.

Usage:
    # Start the worker (from backend/ directory with venv active):
    celery -A services.background.tasks worker --loglevel=info

    # Fire a task from anywhere in the app:
    from services.background.tasks import evaluate_candidate_task
    evaluate_candidate_task.delay(str(session_id))
"""
import logging
from celery import Celery
from config import settings

logger = logging.getLogger(__name__)

# ─── CELERY APP ───────────────────────────────────────────────

celery_app = Celery(
    "sarvam_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,           # re-queue on worker crash
    worker_prefetch_multiplier=1,  # one task at a time per worker
    result_expires=86400,          # results kept for 24 hours
)


# ─── TASKS ────────────────────────────────────────────────────

@celery_app.task(
    name="evaluate_candidate",
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # seconds between retries
)
def evaluate_candidate_task(self, session_id: str):
    """
    Async task: run the full AI evaluation pipeline for a screening session.

    Args:
        session_id: str UUID of the completed ScreeningSession

    This task is fired by POST /screening/complete and runs in the background.
    It calls run_evaluation() which:
      1. Loads transcripts from DB
      2. Translates via Sarvam
      3. Scores 6 competencies
      4. Generates HR audio summary (TTS → S3)
      5. Saves CompetencyScore to DB
    """
    import asyncio
    import uuid
    from core.database import SessionLocal
    from services.pipeline.evaluator import run_evaluation

    logger.info(f"[Task] Starting evaluation for session {session_id}")

    db = SessionLocal()
    try:
        session_uuid = uuid.UUID(session_id)
        score = asyncio.run(run_evaluation(session_uuid, db))

        if score:
            logger.info(f"[Task] Evaluation complete — total score: {score.total_score}")
            return {"status": "completed", "total_score": score.total_score}
        else:
            logger.warning(f"[Task] Evaluation returned None for session {session_id}")
            return {"status": "failed", "reason": "evaluator returned None"}

    except Exception as exc:
        logger.error(f"[Task] Evaluation failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="send_shortlist_notification")
def send_shortlist_notification_task(candidate_id: str, candidate_name: str, job_title: str, score: float, hr_email: str = None):
    """
    Sends an email notification to HR when a candidate is auto-shortlisted.
    """
    from services.email_service import send_hr_new_candidate_alert

    to_email = hr_email or "hr@company.com"
    dashboard_url = f"https://sarvam-talent-discovery-hrdashboard.netlify.app/candidates/{candidate_id}"

    success = send_hr_new_candidate_alert(
        hr_email=to_email,
        candidate_name=candidate_name,
        job_title=job_title,
        total_score=score,
        dashboard_url=dashboard_url,
    )
    if success:
        logger.info(f"[Notify] Email sent to {to_email} for candidate '{candidate_name}'")
        return {"status": "email_sent"}
    else:
        logger.warning(f"[Notify] Email failed or skipped for {to_email}")
        return {"status": "skipped_or_failed"}
