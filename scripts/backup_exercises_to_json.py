#!/usr/bin/env python3
"""Create a timestamped JSON export of exercises collection into db_backups/."""
from datetime import datetime
import json
from btm_workout_db_connect import get_db


def main():
    db = get_db()
    if db is None:
        print("Database not connected.")
        return 1
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = f"db_backups/exercises_backup_{now}.json"
    docs = list(db.exercises.find({}, {"_id": 0}))
    with open(path, "w") as f:
        json.dump(docs, f, indent=2)
    print(f"Wrote {len(docs)} exercises to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
