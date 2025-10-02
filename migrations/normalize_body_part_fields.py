"""Migration helper: normalize body part field names across collections.

This script will:
- In `exercises` collection: rename `bodyPart` -> `body_part` (if present)
- In `body_parts` collection: rename `name` -> `body_part` (if present)

Usage:
  python migrations/normalize_body_part_fields.py        # dry-run summary
  python migrations/normalize_body_part_fields.py --apply  # apply changes

The script is non-destructive by default and prints counts and examples.
"""

import argparse
from btm_workout_db_connect import get_db
import json
import os
import datetime


def collect_stats(db):
    stats = {}

    # exercises: count docs with 'bodyPart' present
    exercises_with_bodyPart = db.exercises.count_documents(
        {"bodyPart": {"$exists": True}}
    )
    stats["exercises_with_bodyPart"] = exercises_with_bodyPart

    # body_parts: count docs with 'name' present and without 'body_part'
    body_parts_with_name = db.body_parts.count_documents({"name": {"$exists": True}})
    stats["body_parts_with_name"] = body_parts_with_name

    # examples (limit 5 each)
    stats["exercises_examples"] = list(
        db.exercises.find({"bodyPart": {"$exists": True}}, {"_id": 0}).limit(5)
    )
    stats["body_parts_examples"] = list(
        db.body_parts.find({"name": {"$exists": True}}, {"_id": 0}).limit(5)
    )

    return stats


def apply_migration(db):
    # exercises: rename field bodyPart -> body_part
    res1 = db.exercises.update_many(
        {"bodyPart": {"$exists": True}}, {"$rename": {"bodyPart": "body_part"}}
    )

    # body_parts: copy field `name` -> `body_part` but do NOT unset `name` here.
    # Unsetting `name` can violate existing unique indexes where missing values are
    # treated as null. We'll preserve `name` during this migration and handle
    # index changes separately if needed.
    cursor = db.body_parts.find({"name": {"$exists": True}})
    updated = 0
    skipped_missing_name = 0
    for doc in cursor:
        _id = doc.get("_id")
        # skip if body_part already exists to avoid overwriting
        if db.body_parts.find_one({"_id": _id, "body_part": {"$exists": True}}):
            continue
        name_val = doc.get("name")
        # If name is None/empty, skip to avoid setting null which may violate indexes
        if name_val is None or (isinstance(name_val, str) and name_val.strip() == ""):
            skipped_missing_name += 1
            continue
        # Set body_part but leave `name` in place for now
        db.body_parts.update_one({"_id": _id}, {"$set": {"body_part": name_val}})
        updated += 1

    return {
        "exercises_renamed_count": res1.modified_count,
        "body_parts_renamed_count": updated,
    }


def export_backup(db, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    # Use timezone-aware UTC timestamp
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for coll in ("exercises", "body_parts", "equipment"):
        docs = list(db[coll].find({}, {"_id": 0}))
        with open(
            os.path.join(out_dir, f"{coll}_backup_{ts}.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true", help="Actually perform the migration"
    )
    parser.add_argument(
        "--backup", action="store_true", help="Export collections before applying"
    )
    args = parser.parse_args()

    db = get_db()
    if db is None:
        print(
            "Database not connected. Set MONGO_URI or MONGO_USER/MONGO_PASS/MONGO_HOST and try again."
        )
        return

    stats = collect_stats(db)
    print("Migration dry-run summary:")
    print(json.dumps(stats, indent=2))

    if not args.apply:
        print("\nDry-run complete. Re-run with --apply to make changes.")
        return

    if args.backup:
        out_dir = f"db_backups/migration_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        print(f"Exporting backups to {out_dir}...")
        export_backup(db, out_dir)

    result = apply_migration(db)
    # include skipped count if present
    if isinstance(result, dict):
        print("Migration applied:")
        print(json.dumps(result, indent=2))
    else:
        print(result)


if __name__ == "__main__":
    main()
