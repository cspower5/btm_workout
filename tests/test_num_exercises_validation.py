import pytest
from flask_server import app


@pytest.fixture
def client():
    return app.test_client()


def test_accepts_snake_case_and_valid_number(client):
    resp = client.post(
        "/api/v1/get_random_exercises", json={"bodyPart": "legs", "num_exercises": 2}
    )
    # No exercises in test DB for 'legs' may be fine; we just want to ensure validation passes
    assert resp.status_code in (200, 404)


def test_accepts_camel_case_and_valid_number(client):
    resp = client.post(
        "/api/v1/get_random_exercises", json={"bodyPart": "legs", "numExercises": 3}
    )
    assert resp.status_code in (200, 404)


def test_invalid_num_exercises_returns_400(client):
    resp = client.post(
        "/api/v1/get_random_exercises", json={"bodyPart": "legs", "numExercises": "abc"}
    )
    assert resp.status_code == 400
    assert resp.get_json().get("error") is not None


def test_missing_body_part_returns_400(client):
    resp = client.post("/api/v1/get_random_exercises", json={"num_exercises": 2})
    assert resp.status_code == 400
    assert resp.get_json().get("error") is not None
