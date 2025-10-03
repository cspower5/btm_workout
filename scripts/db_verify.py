#!/usr/bin/env python3
"""
Run diagnostics against the MongoDB configured for this repo.

Usage:
  # ensure MONGO_URI (or MONGO_USER/MONGO_PASS/MONGO_HOST) is set in env
  python3 scripts/db_verify.py

Output: masked connection info, connected DB name, server info (if permitted),
indexes on `exercises`, document count, a sample doc, and replSet status if allowed.
"""
import os
import re
import sys
import datetime
from pprint import pprint

# Ensure the repository root is on sys.path so we can import btm_workout_db_connect
try:
    from btm_workout_db_connect import get_db, client
except Exception:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        from btm_workout_db_connect import get_db, client
    except Exception:
        print(
            "Failed to import btm_workout_db_connect. Make sure you run this from the repo root and have installed requirements."
        )
        raise


def mask_uri(uri: str) -> str:
    if not uri:
        return None
    return re.sub(r"(mongodb(?:\+srv)?://[^:]+):([^@]+)@", r"\1:***@", uri)


def main():
    raw = os.getenv("MONGO_URI")
    print("Masked MONGO_URI:", mask_uri(raw))

    db = get_db()
    if db is None:
        print("Could not connect to DB. Check env vars and network access.")
        return

    print("Connected DB name:", getattr(db, "name", None))

    # client may be None if connect failed
    try:
        print("Client primary:", getattr(client, "primary", None))
        print("Client nodes:", getattr(client, "nodes", None))
    except Exception:
        print("Client info unavailable")

    try:
        sv = client.server_info()
        print("Server version:", sv.get("version"))
    except Exception:
        print("Server info unavailable")

    print("\nIndexes on exercises:")
    try:
        for i in db.exercises.list_indexes():
            print(" -", i["name"], i.get("key"))
    except Exception:
        print("Could not list indexes")

    try:
        count = db.exercises.count_documents({})
        print("\nexercises count:", count)
    except Exception as e:
        print("Count error:", e)

    try:
        sample = db.exercises.find_one(
            {},
            {"_id": 1, "name": 1, "exercise_name": 1, "body_part": 1, "equipment": 1},
        )
        print("\nSample document:")
        pprint(sample)
    except Exception as e:
        print("Sample fetch error:", e)

    print("\nAttempting replSetGetStatus (may require privileges):")
    try:
        status = client.admin.command("replSetGetStatus")
        primary_optime = None
        for m in status.get("members", []):
            if m.get("stateStr") == "PRIMARY":
                primary_optime = m.get("optimeDate") or m.get("optime", {}).get("ts")
                break
        for m in status.get("members", []):
            name = m.get("name")
            st = m.get("stateStr")
            opt = m.get("optimeDate") or m.get("optime", {}).get("ts")
            lag = None
            if (
                primary_optime
                and opt
                and isinstance(primary_optime, datetime.datetime)
                and isinstance(opt, datetime.datetime)
            ):
                lag = (primary_optime - opt).total_seconds()
            print(f" - {name} {st} optime={opt} lag_s={lag}")
    except Exception as e:
        print("replSetGetStatus failed or not permitted:", e)


if __name__ == "__main__":
    main()
