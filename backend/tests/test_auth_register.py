import pytest
from fastapi.testclient import TestClient
from main import app
from core.database import get_db
from core.models import User
from config import settings
from core.security import hash_password, create_access_token

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


def test_conditional_registration(client, db_session, monkeypatch):
    # Ensure database is clean of active users initially
    db_session.query(User).delete()
    db_session.commit()

    # 1. Cold-start bootstrapping check: should succeed even if ALLOW_PUBLIC_REGISTRATION is False
    monkeypatch.setattr(settings, "ALLOW_PUBLIC_REGISTRATION", False)
    bootstrap_resp = client.post(
        "/auth/register",
        json={"email": "admin@company.com", "password": "password123", "full_name": "Admin User", "role": "admin"}
    )
    assert bootstrap_resp.status_code == 201
    
    # Verify admin was created
    admin_user = db_session.query(User).filter_by(email="admin@company.com").first()
    assert admin_user is not None
    assert admin_user.role == "admin"

    # Create a non-admin HR user in DB for testing
    hr_user = User(
        email="hr@company.com",
        hashed_password=hash_password("password123"),
        full_name="HR User",
        role="hr"
    )
    db_session.add(hr_user)
    db_session.commit()

    # 2. Public registration locked: anonymous register should return 401
    anon_resp = client.post(
        "/auth/register",
        json={"email": "new_hr@company.com", "password": "password123", "full_name": "New HR"}
    )
    assert anon_resp.status_code == 401
    assert "locked" in anon_resp.json()["detail"].lower()

    # 3. Non-admin HR trying to register someone else: should return 403
    hr_token = create_access_token(data={"sub": hr_user.email})
    hr_resp = client.post(
        "/auth/register",
        json={"email": "new_hr@company.com", "password": "password123", "full_name": "New HR"},
        headers={"Authorization": f"Bearer {hr_token}"}
    )
    assert hr_resp.status_code == 403
    assert "administrators" in hr_resp.json()["detail"].lower()

    # 4. Admin registering another user: should succeed (201)
    admin_token = create_access_token(data={"sub": admin_user.email})
    admin_resp = client.post(
        "/auth/register",
        json={"email": "new_hr@company.com", "password": "password123", "full_name": "New HR"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_resp.status_code == 201

    # 5. Public registration allowed: anonymous register should work (201)
    monkeypatch.setattr(settings, "ALLOW_PUBLIC_REGISTRATION", True)
    public_resp = client.post(
        "/auth/register",
        json={"email": "another_hr@company.com", "password": "password123", "full_name": "Another HR"}
    )
    assert public_resp.status_code == 201
