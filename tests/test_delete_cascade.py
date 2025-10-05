import pytest

import flask_server


class FakeDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self, will_delete=0):
        self.will_delete = will_delete
        self.deleted_queries = []

    def delete_one(self, q):
        # store query for inspection
        self.deleted_queries.append(("one", q))
        return FakeDeleteResult(self.will_delete)

    def delete_many(self, q):
        self.deleted_queries.append(("many", q))
        return FakeDeleteResult(self.will_delete)


class FakeDB:
    def __init__(self, bp_deleted=0, eq_deleted=0, ex_deleted=0):
        self.body_parts = FakeCollection(will_delete=bp_deleted)
        self.equipment = FakeCollection(will_delete=eq_deleted)
        self.exercises = FakeCollection(will_delete=ex_deleted)


@pytest.fixture(autouse=True)
def client(monkeypatch):
    # Patch get_db to return a fake DB
    def _get_db():
        # default will be overridden in tests by assigning to flask_server.get_db_return
        return getattr(flask_server, "get_db_return", None)

    monkeypatch.setattr("btm_workout_db_connect.get_db", _get_db, raising=False)

    app = flask_server.app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_delete_body_part_cascade_success(client, monkeypatch):
    # Simulate body part deleted and 3 exercises deleted
    fake_db = FakeDB(bp_deleted=1, ex_deleted=3)
    # attach to module so _get_db reads it
    flask_server.get_db_return = fake_db

    res = client.delete("/api/v1/delete_body_part/legs")
    assert res.status_code == 200
    data = res.get_json()
    assert "Body part" in data["message"]
    assert "3" in data["message"]


def test_delete_body_part_not_found(client):
    fake_db = FakeDB(bp_deleted=0, ex_deleted=0)
    flask_server.get_db_return = fake_db

    res = client.delete("/api/v1/delete_body_part/unknownpart")
    assert res.status_code == 404


def test_delete_equipment_cascade_success(client):
    fake_db = FakeDB(eq_deleted=1, ex_deleted=2)
    flask_server.get_db_return = fake_db

    res = client.delete("/api/v1/delete_equipment/dumbbell")
    assert res.status_code == 200
    data = res.get_json()
    assert "Equipment" in data["message"]
    assert "2" in data["message"]


def test_delete_equipment_not_found(client):
    fake_db = FakeDB(eq_deleted=0, ex_deleted=0)
    flask_server.get_db_return = fake_db

    res = client.delete("/api/v1/delete_equipment/unknown")
    assert res.status_code == 404
