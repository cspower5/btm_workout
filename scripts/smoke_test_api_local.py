#!/usr/bin/env python3
"""
Local smoke test runner that uses Flask's test client and mongomock.

This performs the same sequence as `smoke_test_api.py` but executes in-process
and uses a mongomock database so it won't touch real production data.
"""
import time
import random
import string
import sys

import mongomock

from flask_server import app


def random_suffix(n=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def main():
    # Create a mongomock DB and monkeypatch the db connector used by the app
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["btm_workout_db"]

    import btm_workout_db_connect as db_connect

    # Replace get_db to return our mock
    db_connect.get_db = lambda: mock_db

    suffix = random_suffix()
    test_name = f"smoke-test-{int(time.time())}-{suffix}"

    payload = {
        "exercise_name": test_name,
        "body_part": "smoke-test-bodypart",
        "equipment": "smoke-test-equipment",
        "target": "smoke-test-target",
        "instructions": ["Do this.", "Do that."],
        "difficulty": "Beginner",
    }

    with app.test_client() as client:
        print("[1/4] INSERT /api/v1/insert_exercise")
        r = client.post("/api/v1/insert_exercise", json=payload)
        print("status:", r.status_code)
        print("body:", r.get_json())
        if r.status_code not in (200, 201):
            print("Insert failed")
            sys.exit(1)

        print("[2/4] GET /api/v1/exercise/<name>")
        r = client.get(f"/api/v1/exercise/{test_name}")
        print("status:", r.status_code)
        print("body:", r.get_json())
        if r.status_code != 200:
            print("Get failed")
            sys.exit(1)

        print("[3/4] DELETE /api/v1/delete_exercise/<name>")
        r = client.delete(f"/api/v1/delete_exercise/{test_name}")
        print("status:", r.status_code)
        print("body:", r.get_json())
        if r.status_code not in (200, 202):
            print("Delete failed")
            sys.exit(1)

        print("[4/4] GET (should be 404)")
        r = client.get(f"/api/v1/exercise/{test_name}")
        print("status:", r.status_code)
        print("body:", r.get_json())
        if r.status_code == 404:
            print("Smoke test PASSED")
            sys.exit(0)
        else:
            print("Final GET did not return 404")
            sys.exit(1)


if __name__ == "__main__":
    main()
