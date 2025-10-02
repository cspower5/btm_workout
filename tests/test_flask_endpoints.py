import mongomock
import pytest


import flask_server


@pytest.fixture(autouse=True)
def use_mongo(monkeypatch):
    # Monkeypatch get_db to return a mongomock database
    client = mongomock.MongoClient()
    db = client.get_database("btm_workout_db")

    def fake_get_db():
        return db

    monkeypatch.setattr("btm_workout_db_connect.get_db", fake_get_db)
    yield


def test_health_endpoint():
    client = flask_server.app.test_client()
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_insert_and_get_exercise():
    client = flask_server.app.test_client()
    payload = {
        "exercise_name": "Test Push",
        "body_part": "Chest",
        "equipment": "Body Weight",
        "target": "Pectorals",
    }
    insert_resp = client.post("/api/v1/insert_exercise", json=payload)
    assert insert_resp.status_code == 200
    inserted = insert_resp.get_json()
    assert "id" in inserted

    # Retrieve
    get_resp = client.get("/api/v1/exercise/Test Push")
    assert get_resp.status_code == 200
    got = get_resp.get_json()
    assert got.get("exercise_name") == "Test Push" or got.get("name") == "Test Push"


def test_lists_and_delete():
    client = flask_server.app.test_client()

    # Add a body part and equipment via endpoints
    bp = client.post("/api/v1/add_body_part", json={"name": "Neck"})
    assert bp.status_code == 200
    eq = client.post("/api/v1/add_equipment", json={"name": "Band"})
    assert eq.status_code == 200

    # Add exercise
    payload = {
        "exercise_name": "Neck Stretch",
        "body_part": "Neck",
        "equipment": "Band",
        "target": "Neck",
    }
    r = client.post("/api/v1/insert_exercise", json=payload)
    assert r.status_code == 200

    # Get lists
    bl = client.get("/api/v1/body_parts_list")
    assert bl.status_code == 200
    assert "neck" in [n.lower() for n in bl.get_json()]

    el = client.get("/api/v1/equipment_list")
    assert el.status_code == 200
    assert "band" in [n.lower() for n in el.get_json()]

    xl = client.get("/api/v1/exercises_list")
    assert xl.status_code == 200
    exercises = xl.get_json()
    assert any(
        e
        for e in exercises
        if (e.get("exercise_name") == "Neck Stretch" or e.get("name") == "Neck Stretch")
    )

    # Delete exercise
    delr = client.delete("/api/v1/delete_exercise/Neck Stretch")
    assert delr.status_code == 200
