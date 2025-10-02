"""Detect and optionally merge duplicate body_parts documents.

This script prints groups of `body_part` values that appear in multiple documents
and optionally merges them (keeps the earliest `_id`). When merging, it will
backup affected documents to a timestamped folder and then consolidate fields.

Usage:
  python migrations/detect_and_merge_body_parts.py          # report only
  python migrations/detect_and_merge_body_parts.py --merge  # perform merges (with backup)

Note: Merging is destructive. Use --merge only after reviewing the report.
"""

import argparse
import datetime
import json
import os
from btm_workout_db_connect import get_db


def find_duplicates(db):
    pipeline = [
        {
            "$group": {
                "_id": {"body_part": {"$toLower": "$body_part"}},
                "count": {"$sum": 1},
                "docs": {
                    "$push": {"_id": "$_id", "name": "$name", "body_part": "$body_part"}
                },
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    return list(db.body_parts.aggregate(pipeline))


def backup_docs(db, docs, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(
        os.path.join(out_dir, "body_parts_duplicates.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(docs, f, default=str, ensure_ascii=False, indent=2)


def merge_group(db, group):
    # choose keeper: smallest _id (arbitrary but stable)
    docs = sorted(group["docs"], key=lambda d: str(d["_id"]))
    keeper = docs[0]
    others = docs[1:]
    keeper_id = keeper["_id"]

    # For each other doc, copy any missing fields into keeper, then delete the other
    for doc in others:
        other_id = doc["_id"]
        other_doc = db.body_parts.find_one({"_id": other_id})
        keeper_doc = db.body_parts.find_one({"_id": keeper_id})
        update_fields = {}
        for k, v in other_doc.items():
            if k in ("_id",):
                continue
            if keeper_doc.get(k) in (None, "") and v not in (None, ""):
                update_fields[k] = v
        if update_fields:
            db.body_parts.update_one({"_id": keeper_id}, {"$set": update_fields})
        # Delete the duplicate
        db.body_parts.delete_one({"_id": other_id})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--merge", action="store_true", help="Perform merges (destructive)"
    )
    args = parser.parse_args()

    db = get_db()
    if db is None:
        print(
            "Database not connected. Set MONGO_URI or MONGO_USER/MONGO_PASS/MONGO_HOST and try again."
        )
        return

    groups = find_duplicates(db)
    if not groups:
        print("No duplicate body_part groups found.")
        return

    print(f"Found {len(groups)} duplicate groups:")
    for g in groups:
        print("--")
        print(f"body_part(lower)={g['_id']['body_part']}, count={g['count']}")
        for d in g["docs"]:
            print(
                f"  - _id={d['_id']} name={d.get('name')} body_part={d.get('body_part')}"
            )

    if not args.merge:
        print(
            "\nRun with --merge to consolidate these groups (creates a backup first)."
        )
        return

    # backup before merging
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = f"db_backups/dedupe_body_parts_{ts}"
    print(f"Backing up duplicate groups to {out_dir}...")
    backup_docs(db, groups, out_dir)

    for g in groups:
        print(f"Merging group body_part={g['_id']['body_part']}...")
        merge_group(db, g)

    print(
        "Merge complete. Verify results and consider rebuilding indexes if necessary."
    )


if __name__ == "__main__":
    main()
