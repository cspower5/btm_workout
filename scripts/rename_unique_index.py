#!/usr/bin/env python3
"""
Safely rename the misspelled unique index `unique_exercies_index` to
`unique_exercises_index` on the `exercises` collection.

Usage:
  # dry-run check only
  python scripts/rename_unique_index.py

  # apply the change (create new unique index then drop old)
  python scripts/rename_unique_index.py --apply

This script will:
 - check whether the old index exists
 - verify there are no duplicates for the intended unique key
 - create the correctly-named unique index (if not present)
 - drop the old index if present

Run this from a maintainer account and ensure you have a DB backup before applying.
"""
import argparse
import sys
from pymongo import ASCENDING

# Try to import the project's DB helper. When this script is executed from the
# scripts/ directory the project root may not be on sys.path, so attempt a
# fallback that adds the parent directory to sys.path.
try:
    from btm_workout_db_connect import get_db
except Exception:
    # Add repository root to sys.path and retry
    import os

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        from btm_workout_db_connect import get_db
    except Exception as e:
        print(
            "Failed to import btm_workout_db_connect.get_db. Make sure you run this script from the repo or have the repo root on PYTHONPATH."
        )
        print("Error:", e)
        raise


def has_duplicates(db):
    # Check for duplicate (name, body_part, equipment) combinations
    pipeline = [
        {
            "$group": {
                "_id": {
                    "name": "$name",
                    "body_part": "$body_part",
                    "equipment": "$equipment",
                },
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    dupes = list(db.exercises.aggregate(pipeline))
    return dupes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true", help="Create the new index and drop the old one"
    )
    args = parser.parse_args()

    db = get_db()
    if db is None:
        print(
            "Database connection failed. Set MONGO_URI or credentials in env and try again."
        )
        return

    old_name = "unique_exercies_index"
    new_name = "unique_exercises_index"

    indexes = {idx["name"]: idx for idx in db.exercises.list_indexes()}
    print("Existing indexes:", list(indexes.keys()))

    if new_name in indexes:
        print(f"Index {new_name} already exists. Nothing to do.")
        return

    if old_name not in indexes:
        print(f"Old index {old_name} not found. Creating {new_name} as unique index.")
        if args.apply:
            db.exercises.create_index(
                [
                    ("name", ASCENDING),
                    ("body_part", ASCENDING),
                    ("equipment", ASCENDING),
                ],
                unique=True,
                name=new_name,
            )
            print(f"Created {new_name}.")
        else:
            print("Run with --apply to create the new index.")
        return

    print(f"Old index {old_name} found; checking for duplicates before renaming...")
    dupes = has_duplicates(db)
    if dupes:
        print(f"Found {len(dupes)} duplicate keys. Cannot safely create unique index.")
        for d in dupes[:10]:
            print(d)
        print("Resolve duplicates before running with --apply.")
        return

    print("No duplicates found. Safe to create new unique index.")
    if args.apply:
        db.exercises.create_index(
            [("name", ASCENDING), ("body_part", ASCENDING), ("equipment", ASCENDING)],
            unique=True,
            name=new_name,
        )
        print(f"Created {new_name}.")
        try:
            db.exercises.drop_index(old_name)
            print(f"Dropped old index {old_name}.")
        except Exception as e:
            print(f"Failed to drop {old_name}: {e}")
    else:
        print("Run with --apply to create the new index and drop the old one.")


if __name__ == "__main__":
    main()
