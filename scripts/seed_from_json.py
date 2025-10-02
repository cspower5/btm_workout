#!/usr/bin/env python3
"""Insert exercises from a JSON file into the exercises collection.

Usage:
  python3 scripts/seed_from_json.py path/to/file.json

This will NOT run automatically; it's a helper for manual seeding after backup and review.
"""
import sys
import json
from btm_workout_db_connect import get_db
from pymongo.errors import DuplicateKeyError


def main():
    if len(sys.argv) < 2:
        print("Usage: seed_from_json.py <path-to-json>")
        return 2
    path = sys.argv[1]
    with open(path) as f:
        docs = json.load(f)
    db = get_db()
    if db is None:
        print("Database not connected.")
        return 1
    inserted = 0
    for d in docs:
        try:
            # Ensure canonical fields
            if "name" in d and "exercise_name" not in d:
                d["exercise_name"] = d.pop("name")
            if "bodyPart" in d and "body_part" not in d:
                d["body_part"] = d.pop("bodyPart")
            # Clean legacy fields
            d.pop("name", None)
            d.pop("bodyPart", None)
            db.exercises.insert_one(d)
            inserted += 1
        except DuplicateKeyError:
            print("Duplicate, skipping:", d.get("exercise_name") or d.get("name"))
        except Exception as e:
            print("Error inserting:", e)
    print(f"Inserted {inserted} documents from {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
