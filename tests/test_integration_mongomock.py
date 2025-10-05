import mongomock
import pytest

import btm_workout_db_connect as db_connect
import flask_server


@pytest.fixture(autouse=True)
def use_mongomock(monkeypatch):
    # Create an in-memory mongomock client and database
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["btm_workout_db"]

    # Patch the module-level client and db used by flask_server's get_db()
    monkeypatch.setattr(db_connect, "client", mock_client)
    monkeypatch.setattr(db_connect, "db", mock_db)

    # ensure flask_server.get_db_return isn't interfering
    if hasattr(flask_server, "get_db_return"):
        delattr(flask_server, "get_db_return")

    flask_server.app.config["TESTING"] = True
    with flask_server.app.test_client() as client:
        yield client, mock_db


def test_add_and_delete_body_part_cascade(use_mongomock):
    client, db = use_mongomock

    # Add a body part
    res = client.post("/api/v1/add_body_part", json={"name": "legs"})
    assert res.status_code == 200

    # Insert two exercises that reference body_part 'legs' in different fields
    db.exercises.insert_many(
        [
            {
                "exercise_name": "Test A",
                "name": "test-a",
                "body_part": "legs",
                "equipment": "none",
            },
            {
                "exercise_name": "Test B",
                "name": "test-b",
                "bodyPart": "legs",
                "equipment": "none",
            },
        ]
    )

    # Verify exercises exist
    ex_before = list(db.exercises.find({}, {"_id": 0}))
    assert len(ex_before) == 2

    # Delete the body part (should cascade delete both exercises)
    res = client.delete("/api/v1/delete_body_part/legs")
    assert res.status_code == 200
    data = res.get_json()
    assert "associated exercises" in data["message"]

    # No exercises should remain
    ex_after = list(db.exercises.find({}, {"_id": 0}))
    assert len(ex_after) == 0
