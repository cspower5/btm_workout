"""Export selected MongoDB collections to JSON files.

Usage:
  python scripts/export_db_json.py --outdir ./dump

This script requires accessible MongoDB credentials in env (see .env.example).
"""

import json
from pathlib import Path
from btm_workout_db_connect import get_db


def export_collection(db, collection_name, outdir):
    cursor = db[collection_name].find({})
    out_path = Path(outdir) / f"{collection_name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        docs = []
        for d in cursor:
            # Convert ObjectId to string if present
            d = dict(d)
            if "_id" in d:
                d["_id"] = str(d["_id"])
            docs.append(d)
        json.dump(docs, f, indent=2)
    return out_path


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="./dump")
    args = parser.parse_args()

    db = get_db()
    if db is None:
        print("Error: cannot connect to DB. Set MONGO_URI or local env vars.")
        return

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for col in ["exercises", "body_parts", "equipment"]:
        path = export_collection(db, col, outdir)
        print(f"Exported {col} -> {path}")


if __name__ == "__main__":
    main()
