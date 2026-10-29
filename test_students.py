from datetime import datetime, timedelta, timezone

import jwt

from security import get_jwt_secret
import os

os.environ["STUDENT_API_KEY"] = "test-only-key"
os.environ["JWT_SECRET_KEY"] = (
    "test-only-jwt-secret-at-least-32-characters"
)

import pytest
from fastapi.testclient import TestClient
from security import create_access_token

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session

from app import app
from database import Base, get_db
from models import User
from security import verify_password


@pytest.fixture
def student_client(tmp_path):
    database_url = URL.create(
        "sqlite",
        database=str(tmp_path / "test.db"),
    )

    test_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(test_engine)

    def override_get_db():
        with Session(test_engine) as session:
            yield session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        test_engine.dispose()


def test_student_crud(student_client):
    client = student_client
    headers = {"X-API-Key": "test-only-key"}

    # Create a student.
    response = client.post(
        "/students",
        headers=headers,
        json={"name": "Test Student", "score": 85},
    )
    assert response.status_code == 201
    student_id = response.json()["id"]

    expected = {
        "id": student_id,
        "name": "Test Student",
        "score": 85,
    }

    # Retrieve the saved student.
    response = client.get(
        f"/students/{student_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == expected

    # Check the student appears in the list.
    response = client.get("/students", headers=headers)
    assert response.status_code == 200
    assert response.json() == [expected]

    # Update the score.
    response = client.put(
        f"/students/{student_id}",
        headers=headers,
        json={"name": "Test Student", "score": 90},
    )
    expected["score"] = 90
    assert response.status_code == 200
    assert response.json() == expected

    # Confirm the update was saved.
    response = client.get(
        f"/students/{student_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == expected

    # Delete the student.
    response = client.delete(
        f"/students/{student_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == expected

    # Confirm the student no longer exists.
    response = client.get(
        f"/students/{student_id}",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found"}

    response = client.get("/students", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
def test_registration_and_login(student_client):
    client = student_client
    account = {
        "username": "test_user",
        "password": "Practice-only-Password!",
    }

    response = client.post("/register", json=account)
    assert response.status_code == 201

    user_data = response.json()
    assert user_data["username"] == "test_user"
    assert set(user_data) == {"id", "username"}

    # Verify that the database contains a hash.
    db_override = app.dependency_overrides[get_db]
    session_generator = db_override()

    try:
        db = next(session_generator)
        user = db.get(User, user_data["id"])

        assert user.password_hash != account["password"]
        assert verify_password(
            account["password"],
            user.password_hash,
        )
    finally:
        session_generator.close()

    response = client.post("/register", json=account)
    assert response.status_code == 409

    response = client.post(
        "/login",
        json={
            "username": "test_user",
            "password": "wrong-password",
        },
    )
    assert response.status_code == 401

    response = client.post("/login", json=account)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"

    token = response.json()["access_token"]

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == user_data

    response = client.get("/me")
    assert response.status_code == 401

    response = client.get(
        "/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
@pytest.mark.parametrize("scenario", ["expired", "wrong_secret"])
def test_reject_invalid_tokens(student_client, scenario):
    client = student_client

    response = client.post(
        "/register",
        json={
            "username": "token_test_user",
            "password": "Practice-only-Password!",
        },
    )
    assert response.status_code == 201
    user_id = response.json()["id"]

    now = datetime.now(timezone.utc)
    secret = get_jwt_secret()

    payload = {
        "sub": str(user_id),
        "iat": now - timedelta(minutes=2),
        "exp": now + timedelta(minutes=30),
    }

    # Confirm the user and valid token work first.
    valid_token = jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == user_id

    if scenario == "expired":
        payload["exp"] = now - timedelta(minutes=1)
    else:
        secret = "wrong-test-secret-at-least-32-characters"

    invalid_token = jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired access token"
    }
    assert response.headers["www-authenticate"] == "Bearer"
@pytest.mark.parametrize(
    "role, expected_status",
    [
        ("user", 403),
        ("admin", 200),
    ],
)
def test_admin_permissions(
    student_client,
    role,
    expected_status,
):
    client = student_client

    response = client.post(
        "/register",
        json={
            "username": "permission_test",
            "password": "Practice-only-Password!",
        },
    )
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Check registration creates an ordinary user.
    db_override = app.dependency_overrides[get_db]
    session_generator = db_override()

    try:
        db = next(session_generator)
        user = db.get(User, user_id)

        assert user.role == "user"

        # Set the role for this test scenario.
        user.role = role
        db.commit()
    finally:
        session_generator.close()

    token = create_access_token(user_id)

    response = client.get(
        "/admin/check",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == expected_status

    if role == "admin":
        assert response.json() == {
            "message": "Admin access granted",
            "username": "permission_test",
        }
    else:
        assert response.json() == {
            "detail": "Admin access required"
        }