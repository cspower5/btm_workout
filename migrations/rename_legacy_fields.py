"""Migration script to normalize legacy exercise documents to canonical field names.

This script renames fields in-place in the `exercises` collection:
- `name` -> `exercise_name`
- `bodyPart` -> `body_part`

It supports a dry-run mode and writes a summary of changes. Use with caution and backup your DB before running.
"""

from btm_workout_db_connect import get_db
import argparse
import pprint


def dry_run(db):
    exercises = db.exercises.find(
        {"$or": [{"name": {"$exists": True}}, {"bodyPart": {"$exists": True}}]}
    )
    preview = []
    for ex in exercises:
        preview.append(
            {
                "_id": ex.get("_id"),
                "name": ex.get("name"),
                "bodyPart": ex.get("bodyPart"),
            }
        )
    return preview


def run_migration(db):
    # Rename 'name' -> 'exercise_name' and 'bodyPart' -> 'body_part' for all matching docs
    query = {"$or": [{"name": {"$exists": True}}, {"bodyPart": {"$exists": True}}]}
    cursor = db.exercises.find(query)
    count = 0
    for doc in cursor:
        update = {}
        if "name" in doc:
            update["exercise_name"] = doc["name"]
            update["name"] = None
        if "bodyPart" in doc:
            update["body_part"] = doc["bodyPart"]
            update["bodyPart"] = None

        # Build $set and $unset
        set_ops = {k: v for k, v in update.items() if v is not None}
        unset_ops = {k: "" for k, v in update.items() if v is None}

        ops = {}
        if set_ops:
            ops["$set"] = set_ops
        if unset_ops:
            ops["$unset"] = unset_ops

        if ops:
            db.exercises.update_one({"_id": doc["_id"]}, ops)
            count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Rename legacy exercise fields to canonical names"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show affected documents without applying changes",
    )
    args = parser.parse_args()

    db = get_db()
    if db is None:
        print(
            "Error: could not connect to database. Ensure env vars are set and db is reachable."
        )
        return

    if args.dry_run:
        preview = dry_run(db)
        print("Dry run preview (first 50):")
        pprint.pprint(preview[:50])
        print(f"Total affected documents: {len(preview)}")
        return

    changed = run_migration(db)
    print(f"Migration complete. Documents updated: {changed}")


if __name__ == "__main__":
    main()
