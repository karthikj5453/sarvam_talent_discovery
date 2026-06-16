"""
AI Competency Evaluation Pipeline

Flow:
1. Load screening session transcripts from DB
2. Load job's competency weights
3. Call Sarvam STT-Translate to get English translation of all answers
4. Build scoring prompt with job context + all transcripts
5. Call Sarvam API (or any LLM) to score 6 competency dimensions
6. Generate HR summary text
7. Convert summary to audio via Sarvam TTS
8. Upload summary audio to S3
9. Save CompetencyScore row to DB

Currently uses Sarvam's translate API + a simple scoring heuristic.
In production: swap _call_llm_scorer() for Gemini/GPT-4/Sarvam-105B.
"""
import json
import re
import uuid
import logging
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.models import Candidate, Job, ScreeningSession, CompetencyScore
from services.sarvam.sarvam_client import translate_text, text_to_speech, SarvamError
from services.storage.s3_client import upload_audio, key_to_url

logger = logging.getLogger(__name__)

COMPETENCY_KEYS = [
    "technical_depth",
    "first_principles",
    "shipping_velocity",
    "ownership_signals",
    "curiosity_depth",
    "multilingual_fluency",
]

DEFAULT_WEIGHTS = {
    "technical_depth": 0.25,
    "first_principles": 0.20,
    "shipping_velocity": 0.20,
    "ownership_signals": 0.15,
    "curiosity_depth": 0.10,
    "multilingual_fluency": 0.10,
}


# ─── MAIN ENTRY POINT ─────────────────────────────────────────

async def run_evaluation(session_id: uuid.UUID, db: Session) -> Optional[CompetencyScore]:
    """
    Full async evaluation pipeline. Call this after screening is completed.

    Args:
        session_id: UUID of the completed ScreeningSession
        db:         Active SQLAlchemy session

    Returns:
        CompetencyScore ORM object (also saved to DB), or None on failure.
    """
    # ── 1. Load session + candidate + job ─────────────────────
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        logger.error(f"[Evaluator] Session {session_id} not found")
        return None

    candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
    if not candidate:
        logger.error(f"[Evaluator] Candidate not found for session {session_id}")
        return None

    job = db.query(Job).filter(Job.id == candidate.job_id).first()
    weights = job.competency_weights if job and job.competency_weights else DEFAULT_WEIGHTS

    # ── 2. Collect all transcripts ────────────────────────────
    transcripts = _collect_transcripts(session, candidate)

    # ── 3. Translate to English if needed ────────────────────
    english_text = await _translate_if_needed(transcripts, candidate.detected_language)

    # ── 4. Score competencies ────────────────────────────────
    job_title = job.title if job else "Software Engineer"
    job_skills = job.required_skills if job else []
    scores, justifications, flags = await _score_competencies(
        english_text, job_title, job_skills, weights
    )

    # ── 5. Compute weighted total ─────────────────────────────
    total_score = sum(
        scores.get(k, 0) * weights.get(k, 0) for k in COMPETENCY_KEYS
    )

    # ── 6. Generate HR summary text ──────────────────────────
    hr_summary = _build_hr_summary(candidate, job_title, scores, total_score, flags, justifications)

    # ── 7. Convert summary to audio via Sarvam TTS ───────────
    hr_summary_audio_url = None
    try:
        audio_bytes = await text_to_speech(
            text=hr_summary,
            target_language_code="en-IN",
        )
        s3_key = upload_audio(audio_bytes, str(candidate.id), label="hr_summary")
        hr_summary_audio_url = key_to_url(s3_key)
    except SarvamError as e:
        logger.warning(f"[Evaluator] TTS failed: {e} — continuing without audio")
    except Exception as e:
        logger.warning(f"[Evaluator] S3 upload failed: {e} — continuing without audio")

    # ── 8. Save to DB ─────────────────────────────────────────
    score_row = CompetencyScore(
        candidate_id=candidate.id,
        session_id=session.id,
        technical_depth=scores.get("technical_depth"),
        first_principles=scores.get("first_principles"),
        shipping_velocity=scores.get("shipping_velocity"),
        ownership_signals=scores.get("ownership_signals"),
        curiosity_depth=scores.get("curiosity_depth"),
        multilingual_fluency=scores.get("multilingual_fluency"),
        total_score=round(total_score, 2),
        justifications=justifications,
        flags=flags,
        hr_summary=hr_summary,
        hr_summary_audio_url=hr_summary_audio_url,
        raw_105b_response={"english_transcript": english_text},
    )
    db.add(score_row)

    # Move candidate to shortlisted if score ≥ 6.0
    if total_score >= 6.0:
        candidate.status = "shortlisted"

    db.commit()
    db.refresh(score_row)
    logger.info(f"[Evaluator] Scored candidate {candidate.id}: {total_score:.2f}")
    return score_row


# ─── INTERNAL HELPERS ─────────────────────────────────────────

def _collect_transcripts(session: ScreeningSession, candidate: Candidate) -> dict:
    """Collect all available text from the session."""
    transcripts = {}

    if session.intro_transcript:
        transcripts["intro"] = session.intro_transcript

    answers = session.followup_answers or []
    for i, ans in enumerate(answers):
        if isinstance(ans, dict) and ans.get("transcript"):
            transcripts[f"answer_{i}"] = ans["transcript"]

    return transcripts


async def _translate_if_needed(transcripts: dict, language_code: Optional[str]) -> str:
    """
    If the candidate spoke a non-English language, translate all transcripts.
    Falls back to original text if translation fails.
    """
    combined = "\n\n".join(
        f"[{label.upper()}]\n{text}" for label, text in transcripts.items()
    )

    if not language_code or language_code in ("en-IN", "en-US", "en"):
        return combined

    try:
        translated = await translate_text(
            input_text=combined,
            source_language_code=language_code,
            target_language_code="en-IN",
        )
        return translated
    except SarvamError as e:
        logger.warning(f"[Evaluator] Translation failed ({e}), using original text")
        return combined


async def _score_competencies(
    english_text: str,
    job_title: str,
    required_skills: list,
    weights: dict,
) -> tuple[dict, dict, list]:
    """
    Score the candidate across 6 competency dimensions.

    Currently uses a keyword-heuristic scorer.
    Replace _call_llm_scorer() with a real LLM call for production.

    Returns:
        scores:         {"technical_depth": 7.5, ...}
        justifications: {"technical_depth": "Demonstrated...", ...}
        flags:          ["low_shipping_velocity"]
    """
    return _heuristic_scorer(english_text, required_skills)


def _heuristic_scorer(text: str, required_skills: list) -> tuple[dict, dict, list]:
    """
    Rule-based scorer using keyword signals.
    This is a placeholder — replace with LLM in Phase 4.

    Scoring logic:
    - Check for presence of keywords associated with each competency
    - Length of response signals engagement
    - Skill mentions boost technical_depth
    """
    text_lower = text.lower()
    word_count = len(text.split())

    # Base engagement score (0-3 from length)
    engagement = min(3.0, word_count / 100)

    def signal_score(keywords: list, base: float = 5.0) -> float:
        hits = sum(1 for kw in keywords if kw in text_lower)
        return min(10.0, base + (hits * 0.5) + engagement)

    # Keyword signal maps per dimension
    technical_kws = ["implemented", "built", "architecture", "system", "algorithm",
                     "scale", "performance", "database", "api", "model", "trained",
                     "deployed", "optimized"] + [s.lower() for s in (required_skills or [])]

    first_principles_kws = ["because", "reason", "fundamental", "why", "root cause",
                            "from scratch", "first principles", "underlying", "assumption",
                            "derived", "math", "proof", "logic"]

    shipping_kws = ["shipped", "launched", "deployed", "production", "released",
                    "users", "customers", "delivered", "completed", "live",
                    "in production", "worked on", "finished"]

    ownership_kws = ["i took", "i led", "i owned", "my responsibility", "i initiated",
                     "i decided", "accountability", "proactive", "without being asked",
                     "volunteer", "took charge", "my project"]

    curiosity_kws = ["curious", "learn", "reading", "experimenting", "side project",
                     "interest", "explore", "fascinating", "research", "studying",
                     "hobby", "passionate", "follow", "newsletter"]

    multilingual_kws = ["hindi", "tamil", "telugu", "kannada", "malayalam", "bengali",
                        "language", "communicate", "mother tongue", "native",
                        "translated", "multilingual", "regional"]

    scores = {
        "technical_depth":    round(signal_score(technical_kws, base=4.0), 1),
        "first_principles":   round(signal_score(first_principles_kws, base=4.5), 1),
        "shipping_velocity":  round(signal_score(shipping_kws, base=4.0), 1),
        "ownership_signals":  round(signal_score(ownership_kws, base=4.5), 1),
        "curiosity_depth":    round(signal_score(curiosity_kws, base=4.5), 1),
        "multilingual_fluency": round(signal_score(multilingual_kws, base=5.0), 1),
    }

    justifications = {
        "technical_depth":    f"Score based on technical keyword density and skill mentions in transcript.",
        "first_principles":   f"Score based on reasoning language patterns detected.",
        "shipping_velocity":  f"Score based on delivery and launch keywords in responses.",
        "ownership_signals":  f"Score based on first-person ownership language.",
        "curiosity_depth":    f"Score based on learning and exploration signals.",
        "multilingual_fluency": f"Score based on multilingual context in responses.",
    }

    flags = [k for k, v in scores.items() if v < 5.0]

    return scores, justifications, flags


def _build_hr_summary(
    candidate,
    job_title: str,
    scores: dict,
    total_score: float,
    flags: list,
    justifications: dict,
) -> str:
    """Generate a human-readable HR summary of the evaluation."""
    name = candidate.name or "The candidate"
    language = candidate.detected_language or "English"

    top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    top_str = ", ".join(f"{k.replace('_', ' ').title()} ({v}/10)" for k, v in top_3)

    flag_str = ""
    if flags:
        flag_str = f" Areas needing attention: {', '.join(f.replace('_', ' ') for f in flags)}."

    summary = (
        f"{name} completed the AI screening for {job_title} and scored {total_score:.1f} out of 10. "
        f"The candidate communicated primarily in {language}. "
        f"Top strengths: {top_str}.{flag_str} "
        f"{'This candidate is recommended for shortlisting.' if total_score >= 6.0 else 'Further review is recommended before shortlisting.'}"
    )
    return summary
