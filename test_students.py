from datetime import datetime, timedelta, timezone
from sqlalchemy import select 
from models import Student
from models import RefreshSession
from security import hash_refresh_token
from sqlalchemy.exc import SQLAlchemyError
import jwt

from security import get_jwt_secret
import os


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

    # Create an account in the temporary database.
    response = client.post(
        "/register",
        json={
            "username": "crud_admin",
            "password": "Practice-only-Password!",
        },
    )
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Grant admin permission for this test.
    db_override = app.dependency_overrides[get_db]
    session_generator = db_override()

    try:
        db = next(session_generator)
        user = db.get(User, user_id)
        user.role = "admin"
        db.commit()
    finally:
        session_generator.close()

    token = create_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

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

    # List students.
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

    # Confirm deletion.
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
@pytest.mark.parametrize(
    "method, path",
    [
        ("POST", "/students"),
        ("GET", "/students"),
        ("GET", "/students/{student_id}"),
        ("PUT", "/students/{student_id}"),
        ("DELETE", "/students/{student_id}"),
    ],
)
@pytest.mark.parametrize(
    "caller, expected_status",
    [
        ("anonymous", 401),
        ("api_key_only", 401),
        ("ordinary_user", 403),
    ],
)
def test_student_access_denied(
    student_client,
    method,
    path,
    caller,
    expected_status,
):
    client = student_client

    # Save a student so rejection isn't caused by a missing record.
    db_override = app.dependency_overrides[get_db]
    session_generator = db_override()

    try:
        db = next(session_generator)
        student = Student(name="Protected Student", score=85)
        db.add(student)
        db.commit()
        db.refresh(student)
        student_id = student.id
    finally:
        session_generator.close()

    headers = {}

    if caller == "api_key_only":
        headers = {"X-API-Key": "test-only-key"}

    elif caller == "ordinary_user":
        response = client.post(
            "/register",
            json={
                "username": "ordinary_user",
                "password": "Practice-only-Password!",
            },
        )
        assert response.status_code == 201
        user_id = response.json()["id"]

        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

    request_options = {"headers": headers}

    if method in ("POST", "PUT"):
        request_options["json"] = {
            "name": "Changed Student",
            "score": 90,
        }

    response = client.request(
        method,
        path.format(student_id=student_id),
        **request_options,
    )

    assert response.status_code == expected_status

    expected_detail = (
        "Admin access required"
        if expected_status == 403
        else "Invalid or expired access token"
    )
    assert response.json() == {"detail": expected_detail}

    # Denied requests must leave the saved data unchanged.
    session_generator = db_override()

    try:
        db = next(session_generator)
        students = db.scalars(select(Student)).all()

        assert len(students) == 1
        assert students[0].id == student_id
        assert students[0].name == "Protected Student"
        assert students[0].score == 85
    finally:
        session_generator.close()
def test_refresh_rotation_and_reuse(student_client):
    client = student_client

    account = {
        "username": "refresh_test",
        "password": "Practice-only-Password!",
    }

    # Register and log in.
    response = client.post("/register", json=account)
    assert response.status_code == 201
    user_id = response.json()["id"]

    response = client.post("/login", json=account)
    assert response.status_code == 200
    original_token = response.json()["refresh_token"]

    # Exchange the original refresh token.
    response = client.post(
        "/refresh",
        json={"refresh_token": original_token},
    )
    assert response.status_code == 200

    new_pair = response.json()
    replacement_token = new_pair["refresh_token"]

    assert replacement_token != original_token
    assert new_pair["token_type"] == "bearer"

    # The new access token identifies the correct user.
    response = client.get(
        "/me",
        headers={
            "Authorization": (
                f"Bearer {new_pair['access_token']}"
            )
        },
    )
    assert response.status_code == 200
    assert response.json()["id"] == user_id

    # Reusing the original token revokes its family.
    response = client.post(
        "/refresh",
        json={"refresh_token": original_token},
    )
    assert response.status_code == 401

    # The replacement belongs to the revoked family.
    response = client.post(
        "/refresh",
        json={"refresh_token": replacement_token},
    )
    assert response.status_code == 401
def test_expired_refresh_token(student_client):
    client = student_client

    account = {
        "username": "expiry_test",
        "password": "Practice-only-Password!",
    }

    response = client.post("/register", json=account)
    assert response.status_code == 201

    response = client.post("/login", json=account)
    assert response.status_code == 200
    token = response.json()["refresh_token"]

    # Expire this session in the temporary database.
    db_override = app.dependency_overrides[get_db]
    session_generator = db_override()

    try:
        db = next(session_generator)

        session_record = db.scalar(
            select(RefreshSession).where(
                RefreshSession.token_hash
                == hash_refresh_token(token)
            )
        )
        assert session_record is not None

        session_record.expires_at = (
            int(datetime.now(timezone.utc).timestamp()) - 60
        )
        db.commit()
    finally:
        session_generator.close()

    # An expired refresh token must be rejected.
    response = client.post(
        "/refresh",
        json={"refresh_token": token},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired refresh token"
    }
def test_logout_revokes_only_its_session(student_client):
    client = student_client

    account = {
        "username": "logout_test",
        "password": "Practice-only-Password!",
    }

    response = client.post("/register", json=account)
    assert response.status_code == 201

    # Two logins create separate token families.
    response = client.post("/login", json=account)
    assert response.status_code == 200
    first_pair = response.json()

    response = client.post("/login", json=account)
    assert response.status_code == 200
    second_pair = response.json()

    # Log out the first session.
    response = client.post(
        "/logout",
        json={
            "refresh_token": first_pair["refresh_token"]
        },
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}

    # Repeating logout is harmless.
    response = client.post(
        "/logout",
        json={
            "refresh_token": first_pair["refresh_token"]
        },
    )
    assert response.status_code == 200

    # The first session cannot renew access.
    response = client.post(
        "/refresh",
        json={
            "refresh_token": first_pair["refresh_token"]
        },
    )
    assert response.status_code == 401

    # The separate login remains usable.
    response = client.post(
        "/refresh",
        json={
            "refresh_token": second_pair["refresh_token"]
        },
    )
    assert response.status_code == 200

    # Logout doesn't immediately invalidate an access token.
    response = client.get(
        "/me",
        headers={
            "Authorization": (
                f"Bearer {first_pair['access_token']}"
            )
        },
    )
    assert response.status_code == 200
def test_health(student_client):
    response = student_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness(student_client):
    response = student_client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_database_failure(
    student_client,
    monkeypatch,
):
    class BrokenDatabase:
        def execute(self, statement):
            raise SQLAlchemyError("Simulated database failure")

    def override_failed_db():
        yield BrokenDatabase()

    monkeypatch.setitem(
        app.dependency_overrides,
        get_db,
        override_failed_db,
    )

    response = student_client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Service not ready"
    }

    # The application itself should still respond.
    response = student_client.get("/health")
    assert response.status_code == 200