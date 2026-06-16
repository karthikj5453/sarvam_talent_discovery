import uuid
from core.models import Job, Candidate

def test_db_create_job_and_candidate(db_session):
    # Create Job
    job = Job(
        title="Software Engineer",
        department="Engineering",
        location="Bangalore",
        description="Familiarity with FastAPI",
        required_skills=["FastAPI", "Python"],
        competency_weights={"technical_depth": 0.5}
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    assert job.id is not None
    assert job.title == "Software Engineer"
    
    # Create Candidate
    candidate = Candidate(
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        job_id=job.id,
        status="applied"
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    
    assert candidate.id is not None
    assert candidate.job_id == job.id
    
    # Query back
    fetched = db_session.query(Candidate).filter_by(id=candidate.id).first()
    assert fetched.name == "John Doe"
