#!/usr/bin/env python3
"""Sync distinct body parts from `exercises` collection into `body_parts` collection.

- Finds distinct values from exercises.body_part and exercises.bodyPart (legacy)
- Normalizes to lowercase trimmed names
- Inserts missing names into body_parts collection as documents with `name` field

Usage:
  python3 scripts/sync_body_parts.py

This script uses btm_workout_db_connect.get_db() from the repo to obtain the DB connection.
"""

from btm_workout_db_connect import get_db


def normalize(name):
    return name.strip().lower() if name and isinstance(name, str) else None


def main():
    db = get_db()
    if db is None:
        print('Database not connected. Set MONGO_URI or other env vars and try again.')
        return 1

    exercises = db.exercises
    body_parts_coll = db.body_parts

    # Use distinct() for each field to reliably gather values
    canonical = exercises.distinct('body_part') or []
    legacy = exercises.distinct('bodyPart') or []
    values = set()
    for v in canonical + legacy:
        n = normalize(v)
        if n:
            values.add(n)

    print(f'Found {len(values)} distinct normalized body parts in exercises: {sorted(values)}')

    # Existing body parts in body_parts collection
    existing_cursor = body_parts_coll.find({}, {"_id": 0, "name": 1})
    existing = set()
    for doc in existing_cursor:
        n = normalize(doc.get('name'))
        if n:
            existing.add(n)

    print(f'Found {len(existing)} existing body_parts entries.')

    missing = sorted(values - existing)
    if not missing:
        print('No missing body parts to insert. Database is in sync.')
        return 0

    print('Missing body parts to insert:', missing)

    # Insert missing documents
    docs = [{"name": m} for m in missing]
    result = body_parts_coll.insert_many(docs)
    print(f'Inserted {len(result.inserted_ids)} new body_parts.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
