import os

# Set a test-only key before importing the application.
os.environ["STUDENT_API_KEY"] = "test-only-key"

from fastapi.testclient import TestClient
from app import app


client = TestClient(app)
headers = {"X-API-Key": "test-only-key"}


def test_home():
    response = client.get("/")
    assert response.status_code == 200


def test_missing_key():
    response = client.post(
        "/passing-students",
        json={"scores": {"Alice": 85}}
    )

    assert response.status_code == 401


def test_wrong_key():
    response = client.post(
        "/passing-students",
        headers={"X-API-Key": "wrong-key"},
        json={"scores": {"Alice": 85}}
    )

    assert response.status_code == 401


def test_results_summary():
    response = client.post(
        "/passing-students",
        headers=headers,
        json={
            "scores": {"Alice": 85, "Bob": 42, "John": 55},
            "pass_mark": 60
        }
    )

    assert response.status_code == 200

    assert response.json() == {
        "pass_mark": 60,
        "total_students": 3,
        "passed_count": 1,
        "failed_count": 2,
        "average_score": 60.67,
        "passed": {"Alice": 85},
        "failed": {"Bob": 42, "John": 55}
    }


def test_default_pass_mark_and_boundary():
    response = client.post(
        "/passing-students",
        headers=headers,
        json={"scores": {"Alice": 50, "Bob": 49}}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["pass_mark"] == 50
    assert data["passed"] == {"Alice": 50}
    assert data["failed"] == {"Bob": 49}


def test_empty_scores():
    response = client.post(
        "/passing-students",
        headers=headers,
        json={"scores": {}}
    )

    assert response.status_code == 422


def test_invalid_score():
    response = client.post(
        "/passing-students",
        headers=headers,
        json={"scores": {"Alice": 150}}
    )

    assert response.status_code == 422


def test_invalid_pass_mark():
    response = client.post(
        "/passing-students",
        headers=headers,
        json={
            "scores": {"Alice": 85},
            "pass_mark": -1
        }
    )

    assert response.status_code == 422