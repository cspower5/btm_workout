def test_connect_db_fallback_and_monkeypatch(monkeypatch):
    """Ensure that when MONGO env vars are missing, connect_db falls back to localhost
    and that monkeypatching MongoClient allows connect_db to set db correctly."""

    # Ensure env vars are not set
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("MONGO_USER", raising=False)
    monkeypatch.delenv("MONGO_PASS", raising=False)
    monkeypatch.delenv("MONGO_HOST", raising=False)

    import btm_workout_db_connect as dbc
    import mongomock

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

    # Monkeypatch the MongoClient used in the module
    monkeypatch.setattr(dbc, "MongoClient", DummyClient)

    # Run connect and verify get_db returns a DB object
    dbc.connect_db()
    db = dbc.get_db()
    assert db is not None
