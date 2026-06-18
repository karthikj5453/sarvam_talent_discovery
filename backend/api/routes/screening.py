from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
import logging

from core.database import get_db
from core.models import Candidate, Job, ScreeningSession, CompetencyScore
from core.schemas import (
    ScreeningStartRequest,
    ScreeningSessionResponse,
    ScreeningUploadIntroRequest,
    ScreeningUploadAnswerRequest,
)
from services.sarvam.sarvam_client import transcribe_and_translate, SarvamError
from services.storage.s3_client import upload_audio, upload_resume as s3_upload_resume, key_to_url
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── START SCREENING ──────────────────────────────────────────

@router.post("/start", response_model=ScreeningSessionResponse, status_code=status.HTTP_201_CREATED)
def start_screening(payload: ScreeningStartRequest, db: Session = Depends(get_db)):
    """
    Create a new ScreeningSession for a candidate.
    If an incomplete session already exists, resume it.
    """
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    existing = (
        db.query(ScreeningSession)
        .filter(
            ScreeningSession.candidate_id == payload.candidate_id,
            ScreeningSession.completed_at == None,
        )
        .first()
    )
    if existing:
        return existing

    session = ScreeningSession(candidate_id=payload.candidate_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ─── GET SESSION ──────────────────────────────────────────────

@router.get("/{session_id}", response_model=ScreeningSessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Screening session not found")
    return session


# ─── UPLOAD RESUME ────────────────────────────────────────────

@router.post("/upload-resume")
async def upload_resume(
    candidate_id: UUID = Form(...),
    file: Optional[UploadFile] = File(None),
    resume_url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a resume. Accepts either:
      - A direct file upload (PDF) → uploads to S3/local automatically
      - A pre-uploaded URL string (if client uploaded directly to S3)
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    final_url = resume_url
    file_bytes = None

    if file and not resume_url:
        try:
            file_bytes = await file.read()
            s3_key = s3_upload_resume(file_bytes, str(candidate_id))
            final_url = key_to_url(s3_key)
        except Exception as e:
            logger.warning(f"[Screening] Resume upload failed: {e} — skipping resume URL")
            final_url = None

    if final_url:
        candidate.resume_url = final_url

    # ── Extract text from PDF using PyMuPDF ───────────────────
    if file_bytes:
        try:
            import fitz  # PyMuPDF
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                resume_text = "\n".join(page.get_text() for page in doc).strip()
            if resume_text:
                candidate.resume_text = resume_text[:10000]  # cap at 10k chars
                logger.info(f"[Screening] Extracted {len(resume_text)} chars from resume PDF")
        except Exception as e:
            logger.warning(f"[Screening] PDF text extraction failed: {e}")

    db.commit()
    return {"status": "ok", "resume_url": final_url}


# ─── UPLOAD INTRO AUDIO ───────────────────────────────────────

@router.post("/upload-intro", response_model=ScreeningSessionResponse)
async def upload_intro(
    session_id: UUID = Form(...),
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    detected_language: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Process the candidate's intro audio.

    Two modes:
    1. Send raw audio file → Sarvam STT runs automatically
    2. Send pre-computed transcript text → stored directly

    After saving the transcript, automatically generates AI follow-up
    questions using Gemini and stores them in session.followup_questions.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    final_transcript = transcript
    final_language = detected_language
    intro_audio_url = None

    # ── Case 1: Raw audio → call Sarvam STT ──────────────────
    if file and not transcript:
        audio_bytes = await file.read()

        # Upload to storage for record-keeping
        try:
            s3_key = upload_audio(audio_bytes, str(session.candidate_id), label="intro")
            intro_audio_url = key_to_url(s3_key)
            session.intro_audio_url = intro_audio_url
        except Exception as e:
            logger.warning(f"[Screening] Audio upload failed: {e}")

        # Call Sarvam STT + Translate
        try:
            result = await transcribe_and_translate(
                audio_bytes=audio_bytes,
                filename=file.filename or "intro.wav",
            )
            final_transcript = result.get("transcript", "")
            final_language = result.get("language_code", "unknown")
            logger.info(f"[Screening] STT result: lang={final_language}, chars={len(final_transcript)}")
        except SarvamError as e:
            logger.error(f"[Screening] Sarvam STT failed: {e}")
            raise HTTPException(status_code=502, detail=f"Sarvam STT failed: {e.detail}")

    # ── Save transcript ────────────────────────────────────────
    session.intro_transcript = final_transcript
    session.intro_language = final_language

    if final_language:
        candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
        if candidate:
            candidate.detected_language = final_language

    # ── Generate follow-up questions via Gemini ───────────────
    if final_transcript:
        try:
            candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
            job = db.query(Job).filter(Job.id == candidate.job_id).first() if candidate else None
            job_title = job.title if job else "Software Engineer"
            required_skills = job.required_skills if job else []

            from services.llm.gemini_client import generate_followup_questions
            questions = await generate_followup_questions(
                intro_transcript=final_transcript,
                job_title=job_title,
                required_skills=required_skills,
                n=3,
            )
            session.followup_questions = questions
            logger.info(f"[Screening] Generated {len(questions)} follow-up questions via Gemini")
        except Exception as e:
            # Don't fail the whole intro upload if question generation fails
            logger.warning(f"[Screening] Follow-up question generation failed: {e}")
            session.followup_questions = _default_questions()

    db.commit()
    db.refresh(session)
    return session


def _default_questions() -> list:
    """Generic fallback questions when AI generation is unavailable."""
    return [
        "Tell me about a challenging technical problem you solved recently.",
        "Describe a project where you had to make an important architectural decision.",
        "How do you approach debugging a production issue you've never seen before?",
    ]


# ─── UPLOAD ANSWER AUDIO ──────────────────────────────────────

@router.post("/upload-answer", response_model=ScreeningSessionResponse)
async def upload_answer(
    session_id: UUID = Form(...),
    question_index: int = Form(...),
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Process one follow-up answer audio.
    question_index is 0-based, matching the followup_questions array.
    Like upload-intro: accepts raw audio (→ Sarvam STT) or pre-computed transcript.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    final_transcript = transcript
    answer_audio_url = None

    # ── Case 1: Raw audio → Sarvam STT ───────────────────────
    if file and not transcript:
        audio_bytes = await file.read()

        try:
            s3_key = upload_audio(audio_bytes, str(session.candidate_id), label=f"answer_{question_index}")
            answer_audio_url = key_to_url(s3_key)
        except Exception as e:
            logger.warning(f"[Screening] S3 answer upload failed: {e}")

        try:
            result = await transcribe_and_translate(
                audio_bytes=audio_bytes,
                filename=file.filename or "answer.wav",
            )
            final_transcript = result.get("transcript", "")
        except SarvamError as e:
            logger.error(f"[Screening] Sarvam STT (answer) failed: {e}")
            raise HTTPException(status_code=502, detail=f"Sarvam STT failed: {e.detail}")

    # ── Update answers list ───────────────────────────────────
    answers: list = list(session.followup_answers or [])
    while len(answers) <= question_index:
        answers.append({})

    answers[question_index] = {
        "transcript": final_transcript,
        "answer_audio_url": answer_audio_url,
    }

    session.followup_answers = answers
    db.commit()
    db.refresh(session)
    return session


# ─── COMPLETE SCREENING ───────────────────────────────────────

@router.post("/complete", response_model=ScreeningSessionResponse)
async def complete_screening(session_id: UUID, db: Session = Depends(get_db)):
    """
    Mark the session complete → update candidate status → fire AI evaluation.

    Evaluation mode (set via ASYNC_EVAL in .env):
      - ASYNC_EVAL=false (default): runs evaluation synchronously before returning.
      - ASYNC_EVAL=true:            queues a Celery background task and returns immediately.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.completed_at:
        raise HTTPException(status_code=400, detail="Session already completed")

    session.completed_at = datetime.now(timezone.utc)

    candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
    if candidate:
        candidate.status = "screened"

    db.commit()
    db.refresh(session)

    # ── Fire evaluation ───────────────────────────────────────
    if settings.ASYNC_EVAL:
        # Production: Celery background task
        try:
            from services.background.tasks import evaluate_candidate_task
            evaluate_candidate_task.delay(str(session_id))
            logger.info(f"[Screening] Evaluation task queued for session {session_id}")
        except Exception as e:
            logger.warning(f"[Screening] Could not queue evaluation task: {e}")
    else:
        # Dev mode: run synchronously
        try:
            from services.pipeline.evaluator import run_evaluation
            logger.info(f"[Screening] Running evaluation synchronously for session {session_id}")
            score = await run_evaluation(session.id, db)
            if score:
                logger.info(f"[Screening] Evaluation complete — score: {score.total_score}")
            else:
                logger.warning(f"[Screening] Evaluation returned None for session {session_id}")
        except Exception as e:
            # Don't fail the /complete endpoint if evaluation crashes
            logger.error(f"[Screening] Evaluation error: {e}", exc_info=True)

    # Refresh session after evaluation may have updated candidate status
    db.refresh(session)
    return session