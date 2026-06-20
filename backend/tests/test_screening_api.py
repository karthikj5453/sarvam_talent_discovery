import pytest
from fastapi.testclient import TestClient
from main import app
from core.database import get_db
from core.models import Job, Candidate, ScreeningSession, User
from core.security import create_access_token

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


def test_delete_candidate(client, db_session):
    # 1. Create a user for authentication
    user = User(
        email="hr_test@company.com",
        hashed_password="hashed_placeholder",
        full_name="HR Test User",
        role="hr"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Job and Candidate to delete
    job = Job(
        title="Python Developer",
        required_skills=["Python"],
        competency_weights={"technical_depth": 0.5}
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    candidate = Candidate(
        name="Candidate to Delete",
        email="delete_me@example.com",
        phone="9876543210",
        job_id=job.id,
        status="applied",
        consent_given=True
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    # Add a screening session for candidate
    session = ScreeningSession(candidate_id=candidate.id)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # 3. Call DELETE candidate endpoint
    delete_resp = client.delete(f"/candidates/{candidate.id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"

    # 4. Verify candidate and session are deleted from DB
    deleted_cand = db_session.query(Candidate).filter(Candidate.id == candidate.id).first()
    assert deleted_cand is None
    deleted_sess = db_session.query(ScreeningSession).filter(ScreeningSession.candidate_id == candidate.id).first()
    assert deleted_sess is None


def test_get_session_job(client, db_session):
    # Create Job and Candidate
    job = Job(
        title="Engineering Manager",
        required_skills=["Management"],
        competency_weights={"ownership_signals": 0.5}
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    candidate = Candidate(
        name="Candidate For Job Test",
        email="job_test@example.com",
        phone="9876543210",
        job_id=job.id,
        status="applied",
        consent_given=True
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    # Create Screening Session
    session = ScreeningSession(candidate_id=candidate.id)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # Fetch job info via secure public endpoint
    resp = client.get(f"/screening/{session.id}/job")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Engineering Manager"
    assert "id" in data
