import pytest
import uuid
from unittest.mock import MagicMock
from core.models import Job, Candidate, ScreeningSession, CompetencyScore
from services.pipeline.evaluator import run_evaluation
import services.pipeline.evaluator as evaluator_module

@pytest.mark.anyio
async def test_run_evaluation_pipeline(db_session, monkeypatch):
    # 1. Create a test job
    job = Job(
        title="Python AI Developer",
        department="Engineering",
        location="Bangalore",
        description="Build LLM applications and APIs",
        required_skills=["Python", "FastAPI", "Docker"],
        competency_weights={
            "technical_depth": 0.3,
            "first_principles": 0.2,
            "shipping_velocity": 0.2,
            "ownership_signals": 0.1,
            "curiosity_depth": 0.1,
            "multilingual_fluency": 0.1,
        }
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    # 2. Create a candidate
    candidate = Candidate(
        name="Aarav Sharma",
        email="aarav@example.com",
        phone="9876543210",
        job_id=job.id,
        status="applied",
        detected_language="hi-IN"
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    
    # 3. Create a screening session with some transcripts
    session = ScreeningSession(
        candidate_id=candidate.id,
        intro_transcript="नमस्ते, मेरा नाम आरव है और मैं एक पाइथन डेवलपर हूँ। मुझे नए सिस्टम्स बनाना अच्छा लगता है।",
        intro_language="hi-IN",
        followup_questions=[
            {"question": "Tell me about a complex project you shipped."},
            {"question": "Explain how database indexing works from first principles."}
        ],
        followup_answers=[
            {"transcript": "मैंने एक नया एपीआई डिप्लॉय किया था जो कि बहुत फास्ट चलता है।", "answer_audio_url": "s3://mock/answer_0.wav"},
            {"transcript": "डेटाबेस इंडेक्सिंग एक किताब के अंत में दी गई इंडेक्स टेबल की तरह होती है।", "answer_audio_url": "s3://mock/answer_1.wav"}
        ]
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    # 4. Mock the translation call (since language is hi-IN)
    async def mock_translate_text(input_text, source_language_code, target_language_code):
        # Return a mock English translation containing keywords for scoring
        return (
            "[INTRO]\nHello, my name is Aarav and I am a Python developer. I love building new systems.\n\n"
            "[ANSWER_0]\nI deployed and shipped a new API that works very fast in production.\n\n"
            "[ANSWER_1]\nDatabase indexing works because it avoids full table scans. It is a fundamental root cause search structure from scratch."
        )
    monkeypatch.setattr(evaluator_module, "translate_text", mock_translate_text)
    
    # 5. Mock the text_to_speech call
    async def mock_text_to_speech(text, target_language_code):
        return b"mock-tts-audio-bytes"
    monkeypatch.setattr(evaluator_module, "text_to_speech", mock_text_to_speech)
    
    # 6. Mock the S3 upload audio call
    def mock_upload_audio(audio_bytes, candidate_id, label):
        return f"audio/{candidate_id}_{label}.wav"
    monkeypatch.setattr(evaluator_module, "upload_audio", mock_upload_audio)
    
    # 7. Run evaluation
    score_row = await run_evaluation(session.id, db_session)
    
    assert score_row is not None
    assert score_row.candidate_id == candidate.id
    assert score_row.session_id == session.id
    assert score_row.total_score >= 0.0
    
    # Check that justifications are present
    assert "technical_depth" in score_row.justifications
    
    # Check that candidate status got updated to shortlisted if total_score >= 6.0
    db_session.refresh(candidate)
    if score_row.total_score >= 6.0:
        assert candidate.status == "shortlisted"
    else:
        assert candidate.status == "screened"
