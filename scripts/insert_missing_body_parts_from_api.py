#!/usr/bin/env python3
"""Fetch exercises from the public API, compute distinct body parts, and insert any missing
names into the `body_parts` collection in the DB.

This is a safe, idempotent operation: it only inserts missing lowercased names.
"""
import requests
from btm_workout_db_connect import get_db


def normalize(name):
    return name.strip().lower() if name and isinstance(name, str) else None


def main():
    API = 'https://btm-workout.onrender.com'
    resp = requests.get(f'{API}/api/v1/exercises_list', timeout=30)
    resp.raise_for_status()
    exercises = resp.json()

    parts = set()
    for d in exercises:
        if 'body_part' in d and d['body_part']:
            parts.add(normalize(d['body_part']))
        elif 'bodyPart' in d and d['bodyPart']:
            parts.add(normalize(d['bodyPart']))

    parts.discard(None)
    print(f'API returned {len(exercises)} exercises and {len(parts)} distinct normalized body parts.')

    db = get_db()
    if db is None:
        print('Database not connected')
        return 2

    existing = set()
    for doc in db.body_parts.find({}, {'_id': 0, 'name': 1}):
        n = normalize(doc.get('name'))
        if n:
            existing.add(n)

    missing = sorted(parts - existing)
    if not missing:
        print('No missing body parts to insert.'); return 0

    print('Inserting missing body parts:', missing)
    docs = [{'name': m} for m in missing]
    result = db.body_parts.insert_many(docs)
    print(f'Inserted {len(result.inserted_ids)} body_parts: {missing}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
