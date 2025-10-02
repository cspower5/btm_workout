"""Finalize body_part migration: unset `name` only where safe.

This script will:
- Detect documents where `body_part` exists and `name` also exists.
- Ensure unsetting `name` will not violate the existing unique index (by checking for
  other documents that would collide on the `name` index when set to null).
- Unset `name` for safe documents.

Usage:
  python migrations/finalize_body_part_migration.py        # dry-run summary
  python migrations/finalize_body_part_migration.py --apply --backup  # backup + apply
"""

import argparse
import datetime
import json
import os
from btm_workout_db_connect import get_db


def find_candidates(db):
    # Docs that have both name and body_part
    return list(
        db.body_parts.find({"name": {"$exists": True}, "body_part": {"$exists": True}})
    )


def is_safe_to_unset(db, doc):
    # If unsetting `name` would cause a duplicate null in the unique index on `name`,
    # it would show up as another document with missing/None `name`. We'll treat
    # None/absent/empty as potential duplicates; so it's safe only if no other doc
    # (excluding self) has name==None or name does not exist.
    query = {
        "_id": {"$ne": doc["_id"]},
        "$or": [{"name": None}, {"name": {"$exists": False}}, {"name": ""}],
    }
    return db.body_parts.count_documents(query) == 0


def export_backup(db, docs, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(
        os.path.join(out_dir, "finalize_candidates.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(docs, f, default=str, ensure_ascii=False, indent=2)


def apply_finalize(db, candidates):
    updated = 0
    skipped = 0
    for doc in candidates:
        if is_safe_to_unset(db, doc):
            db.body_parts.update_one({"_id": doc["_id"]}, {"$unset": {"name": ""}})
            updated += 1
        else:
            skipped += 1
    return {"finalize_unset_count": updated, "skipped_due_to_index_risk": skipped}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true", help="Actually unset name where safe"
    )
    parser.add_argument(
        "--backup", action="store_true", help="Export candidates before applying"
    )
    args = parser.parse_args()

    db = get_db()
    if db is None:
        print(
            "Database not connected. Set MONGO_URI or MONGO_USER/MONGO_PASS/MONGO_HOST and try again."
        )
        return

    candidates = find_candidates(db)
    print(f"Found {len(candidates)} candidate documents with both name and body_part.")
    for c in candidates:
        print(
            f" - _id={c.get('_id')} name={c.get('name')} body_part={c.get('body_part')}"
        )

    if not args.apply:
        print(
            "Dry-run complete. Re-run with --apply --backup to export and unset where safe."
        )
        return

    if args.backup:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = f"db_backups/finalize_body_part_{ts}"
        print(f"Exporting candidate docs to {out_dir}...")
        export_backup(db, candidates, out_dir)

    result = apply_finalize(db, candidates)
    print("Finalize result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
