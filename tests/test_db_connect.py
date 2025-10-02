import mongomock


def test_get_db_mock(monkeypatch):
    # Provide a fake MongoClient via monkeypatching MongoClient in btm_workout_db_connect
    import btm_workout_db_connect as dbc

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self._db = mongomock.MongoClient().db

        def get_database(self, name):
            return self._db

        @property
        def admin(self):
            return self

        def command(self, *args, **kwargs):
            return {"ok": 1}

    monkeypatch.setattr(dbc, "MongoClient", DummyClient)

    # Ensure connect_db uses the monkeypatched client
    dbc.connect_db()
    db = dbc.get_db()
    assert db is not None
