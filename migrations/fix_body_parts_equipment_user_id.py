"""
Migration: Fix body_parts and equipment user_id field + Update indexes

This migration:
1. Converts ObjectId user_id values to "public" string in body_parts and equipment
2. Updates indexes to use snake_case field names (user_id, name) instead of camelCase

Run this script to:
- Update all body_parts and equipment documents to use user_id="public"
- Recreate indexes with correct field names for user isolation
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from btm_workout_db_connect import get_db
from datetime import datetime
from pymongo import ASCENDING
import json


def backup_collections():
    """Backup body_parts and equipment collections before migration"""
    db = get_db()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_dir = f"db_backups/fix_user_id_{timestamp}"

    os.makedirs(backup_dir, exist_ok=True)

    # Backup body_parts
    body_parts = list(db.body_parts.find({}))
    with open(f"{backup_dir}/body_parts_before.json", "w") as f:
        json.dump(body_parts, f, indent=2, default=str)

    # Backup equipment
    equipment = list(db.equipment.find({}))
    with open(f"{backup_dir}/equipment_before.json", "w") as f:
        json.dump(equipment, f, indent=2, default=str)

    print(f"✅ Backup created in {backup_dir}")
    print(f"   - body_parts: {len(body_parts)} documents")
    print(f"   - equipment: {len(equipment)} documents")

    return backup_dir


def migrate_body_parts_and_equipment():
    """Update all body_parts and equipment to have user_id='public'"""
    db = get_db()

    print("\n=== Before Migration ===")
    print(f"body_parts total: {db.body_parts.count_documents({})}")
    print(
        f"body_parts with user_id='public': {db.body_parts.count_documents({'user_id': 'public'})}"
    )
    print(f"equipment total: {db.equipment.count_documents({})}")
    print(
        f"equipment with user_id='public': {db.equipment.count_documents({'user_id': 'public'})}"
    )

    # Sample before
    print("\n=== Sample Before (body_parts) ===")
    sample_bp = db.body_parts.find_one()
    if sample_bp:
        print(f"  user_id type: {type(sample_bp.get('user_id'))}")
        print(f"  user_id value: {sample_bp.get('user_id')}")

    # Update body_parts
    result_bp = db.body_parts.update_many(
        {}, {"$set": {"user_id": "public"}}  # All documents
    )

    # Update equipment
    result_eq = db.equipment.update_many(
        {}, {"$set": {"user_id": "public"}}  # All documents
    )

    print("\n=== Migration Results ===")
    print(f"✅ Updated {result_bp.modified_count} body_parts documents")
    print(f"✅ Updated {result_eq.modified_count} equipment documents")

    print("\n=== After Migration ===")
    print(
        f"body_parts with user_id='public': {db.body_parts.count_documents({'user_id': 'public'})}"
    )
    print(
        f"equipment with user_id='public': {db.equipment.count_documents({'user_id': 'public'})}"
    )

    # Sample after
    print("\n=== Sample After (body_parts) ===")
    for bp in db.body_parts.find().limit(3):
        print(
            f"  {bp.get('name')}: user_id={bp.get('user_id')} (type: {type(bp.get('user_id')).__name__})"
        )

    print("\n=== Sample After (equipment) ===")
    for eq in db.equipment.find().limit(3):
        print(
            f"  {eq.get('name')}: user_id={eq.get('user_id')} (type: {type(eq.get('user_id')).__name__})"
        )


def update_indexes():
    """Update indexes to use snake_case field names"""
    db = get_db()

    print("\n\n=== Updating Indexes ===")

    # --- Exercises Index ---
    print("\n1. Exercises collection:")
    try:
        db.exercises.drop_index("unique_exercises_index")
        print("   ✅ Dropped old exercises index")
    except Exception as e:
        print(f"   ℹ️  No old index to drop: {e}")

    db.exercises.create_index(
        [
            ("name", ASCENDING),
            ("body_part", ASCENDING),
            ("equipment", ASCENDING),
            ("user_id", ASCENDING),
        ],
        unique=True,
        name="unique_exercises_index",
    )
    print("   ✅ Created new index: (name, body_part, equipment, user_id)")

    # --- Body Parts Index ---
    print("\n2. Body parts collection:")
    # Try multiple possible old index names
    for old_index in ["unique_body_parts_index", "unique_body_part_index"]:
        try:
            db.body_parts.drop_index(old_index)
            print(f"   ✅ Dropped old body_parts index: {old_index}")
        except Exception:
            print(f"   ℹ️  No index named '{old_index}' to drop")

    db.body_parts.create_index(
        [("name", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="unique_body_parts_index",
    )
    print("   ✅ Created new index: (name, user_id)")

    # --- Equipment Index ---
    print("\n3. Equipment collection:")
    try:
        db.equipment.drop_index("unique_equipment_index")
        print("   ✅ Dropped old equipment index")
    except Exception as e:
        print(f"   ℹ️  No old index to drop: {e}")

    db.equipment.create_index(
        [("name", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="unique_equipment_index",
    )
    print("   ✅ Created new index: (name, user_id)")

    print("\n✅ All indexes updated successfully!")


if __name__ == "__main__":
    print("=" * 70)
    print("Migration: Fix body_parts/equipment user_id + Update indexes")
    print("=" * 70)

    # Backup first
    backup_dir = backup_collections()

    # Run data migration
    migrate_body_parts_and_equipment()

    # Update indexes
    update_indexes()

    print("\n" + "=" * 70)
    print(f"✅ Migration complete! Backup saved to: {backup_dir}")
    print("=" * 70)
