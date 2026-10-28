import os

os.environ["STUDENT_API_KEY"] = "test-only-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session

from app import app
from database import Base, get_db


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