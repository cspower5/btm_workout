import mongomock
import pytest

from flask_server import app


@pytest.fixture
def client(monkeypatch):
    # Create a mongomock client and patch the app/db connector to use it
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["btm_workout_db"]

    # Monkeypatch the get_db function used by flask_server via btm_workout_db_connect
    import btm_workout_db_connect as db_connect

    monkeypatch.setattr(db_connect, "get_db", lambda: mock_db)

    with app.test_client() as c:
        yield c


def test_insert_preserves_display_and_normalizes(client):
    payload = {
        "exercise_name": "Test Push",
        "body_part": "Chest ",
        "equipment": " Body Weight",
        "target": "Pectorals",
    }

    # Register and get token
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser3",
            "email": "testuser3@example.com",
            "password": "testpass123",
        },
    )
    assert reg_resp.status_code == 200 or reg_resp.status_code == 201
    token = reg_resp.get_json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Insert the exercise
    resp = client.post("/api/v1/insert_exercise", json=payload, headers=headers)
    assert resp.status_code == 200 or resp.status_code == 201

    # Access the mocked DB from the patched connector directly
    from btm_workout_db_connect import get_db

    stored = get_db().exercises.find_one({})
    assert stored is not None

    # Display name preserved
    assert stored.get("exercise_name") == "Test Push"

    # Normalized fields exist and are lowercase/stripped
    assert stored.get("name") == "test push"
    assert stored.get("body_part") == "chest"
    assert stored.get("equipment") == "body weight"
