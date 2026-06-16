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
        status="applied"
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
    complete_resp = client.post(f"/screening/complete?session_id={session_id}")
    assert complete_resp.status_code == 200
    assert complete_resp.json()["completed_at"] is not None

    # Check candidate status update
    db_session.refresh(candidate)
    assert candidate.status == "screened"
