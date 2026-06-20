import pytest
from fastapi.testclient import TestClient
from main import app
from core.database import get_db
from core.models import Job, Candidate, ScreeningSession

# We will override get_db to return our session-managed db_session fixture.
# Since db_session is function-scoped, the override will be clean for each test.

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_screening_api_flow(client, db_session):
    # 1. Create Job and Candidate first
    job = Job(
        title="Frontend Architect",
        required_skills=["React", "CSS"],
        competency_weights={"technical_depth": 0.5}
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    candidate = Candidate(
        name="Preeti Patel",
        email="preeti@example.com",
        phone="9876500000",
        job_id=job.id,
        status="applied",
        consent_given=True
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    # 2. Test /screening/start
    start_resp = client.post("/screening/start", json={"candidate_id": str(candidate.id)})
    assert start_resp.status_code == 201
    session_data = start_resp.json()
    assert session_data["candidate_id"] == str(candidate.id)
    session_id = session_data["id"]

    # 3. Test /screening/upload-intro (with text transcript)
    intro_resp = client.post(
        "/screening/upload-intro",
        data={
            "session_id": session_id,
            "transcript": "Hello, I am Preeti. I have been building user interfaces with React and CSS for 5 years.",
            "detected_language": "en-US"
        }
    )
    assert intro_resp.status_code == 200
    assert intro_resp.json()["intro_transcript"] == "Hello, I am Preeti. I have been building user interfaces with React and CSS for 5 years."

    # 4. Test /screening/upload-answer (with text transcript)
    answer_resp = client.post(
        "/screening/upload-answer",
        data={
            "session_id": session_id,
            "question_index": 0,
            "transcript": "I designed a modular design system that reduced CSS size by 40%."
        }
    )
    assert answer_resp.status_code == 200
    answers = answer_resp.json()["followup_answers"]
    assert len(answers) == 1
    assert answers[0]["transcript"] == "I designed a modular design system that reduced CSS size by 40%."

    # 5. Test /screening/complete
    complete_resp = client.post(f"/screening/complete/{session_id}")
    assert complete_resp.status_code == 200
    assert complete_resp.json()["completed_at"] is not None

    # Check candidate status update
    db_session.refresh(candidate)
    assert candidate.status == "screened"


def test_candidate_apply_consent_flow(client, db_session):
    # Create a job
    job = Job(
        title="Software Engineer",
        required_skills=["Python"],
        competency_weights={"technical_depth": 0.5}
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # 1. Apply without consent (consent_given=False)
    apply_resp_no_consent = client.post(
        "/candidates/public/apply",
        json={
            "name": "No Consent Cand",
            "email": "noconsent@example.com",
            "phone": "1234567890",
            "job_id": str(job.id),
            "consent_given": False
        }
    )
    assert apply_resp_no_consent.status_code == 201
    cand_no_consent = apply_resp_no_consent.json()

    # Verify that starting screening fails
    start_no_consent = client.post("/screening/start", json={"candidate_id": cand_no_consent["id"]})
    assert start_no_consent.status_code == 403
    assert "Consent must be recorded" in start_no_consent.json()["detail"]

    # 2. Apply with consent (consent_given=True)
    apply_resp_with_consent = client.post(
        "/candidates/public/apply",
        json={
            "name": "Consent Cand",
            "email": "consent@example.com",
            "phone": "9876543210",
            "job_id": str(job.id),
            "consent_given": True
        }
    )
    assert apply_resp_with_consent.status_code == 201
    cand_with_consent = apply_resp_with_consent.json()

    # Verify that starting screening succeeds
    start_with_consent = client.post("/screening/start", json={"candidate_id": cand_with_consent["id"]})
    assert start_with_consent.status_code == 201
