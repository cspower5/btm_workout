"""Replace existing `unique_body_part_name` index with a `unique_body_part` index.

This script will:
- Inspect the current indexes on `body_parts`.
- If an index named `unique_body_part_name` exists, optionally drop it.
- Create a new unique index on the `body_part` field (sparse to avoid null collisions).

Usage:
  python migrations/replace_body_part_index.py        # dry-run: show indexes and what would change
  python migrations/replace_body_part_index.py --apply  # perform the index replacement

Notes:
- Sparse unique indexes treat absent fields as missing and allow multiple docs without the field.
- If you prefer a partial index (only enforce uniqueness for non-null values), we can create a partial index instead.
"""

import argparse
from btm_workout_db_connect import get_db
import json


def show_indexes(db):
    idx = db.body_parts.index_information()
    return idx


def replace_index(db):
    info = show_indexes(db)
    # look for a likely existing index name
    to_drop = None
    for name, spec in info.items():
        # Heuristic: index on 'name' field and unique
        if any(
            k == ("name", 1) or k == ("name", -1) for k in spec.get("key", [])
        ) and spec.get("unique"):
            to_drop = name
            break

    result = {"existing_indexes": info, "dropped_index": None, "created_index": None}

    if to_drop:
        db.body_parts.drop_index(to_drop)
        result["dropped_index"] = to_drop

    # Create a unique partial index on body_part where body_part exists and is not null
    # MongoDB partial filter expression ensures uniqueness only for documents with a non-null body_part.
    new_name = db.body_parts.create_index(
        [("body_part", 1)],
        unique=True,
        name="unique_body_part",
        partialFilterExpression={"body_part": {"$exists": True, "$ne": None}},
    )
    result["created_index"] = new_name
    result["indexes_after"] = db.body_parts.index_information()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true", help="Perform the index replacement"
    )
    args = parser.parse_args()

    db = get_db()
    if db is None:
        print("Database not connected")
        return

    print("Current indexes on body_parts:")
    info = show_indexes(db)
    print(json.dumps(info, default=str, indent=2))

    if not args.apply:
        print(
            "\nDry-run complete. Re-run with --apply to drop the old index (if found) and create the new index."
        )
        return

    print("Applying index replacement...")
    res = replace_index(db)
    print(json.dumps(res, default=str, indent=2))


if __name__ == "__main__":
    main()
