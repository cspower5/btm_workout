#!/usr/bin/env python3
"""
Migration script to standardize field names across all collections.

Changes:
1. exercises: Remove 'exercise_name' field (use 'name' only), rename 'userId' to 'user_id'
2. body_parts: Rename 'userId' to 'user_id'
3. equipment: Rename 'userId' to 'user_id'
4. hidden_items: Rename 'userId' to 'user_id', 'itemType' to 'item_type', 'itemName' to 'item_name'

This ensures consistency with Atlas indexes and snake_case naming convention.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from btm_workout_db_connect import get_db
from datetime import datetime


def backup_collection(db, collection_name):
    """Backup collection before migration"""
    collection = db[collection_name]
    backup_name = (
        f"{collection_name}_backup_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    )

    print(f"📦 Creating backup: {backup_name}")

    # Create backup collection
    docs = list(collection.find({}))
    if docs:
        db[backup_name].insert_many(docs)
        print(f"✅ Backed up {len(docs)} documents to {backup_name}")
    else:
        print(f"ℹ️  No documents to backup in {collection_name}")

    return backup_name


def migrate_exercises(db):
    """
    Migrate exercises collection:
    - Remove 'exercise_name' field
    - Rename 'userId' to 'user_id'
    """
    print("\n=== Migrating exercises collection ===")

    collection = db.exercises

    # Backup first
    backup_collection(db, "exercises")

    # Count documents with exercise_name or userId
    docs_with_exercise_name = collection.count_documents(
        {"exercise_name": {"$exists": True}}
    )
    docs_with_userId = collection.count_documents({"userId": {"$exists": True}})

    print(f"Found {docs_with_exercise_name} documents with 'exercise_name' field")
    print(f"Found {docs_with_userId} documents with 'userId' field")

    # Step 1: Remove exercise_name field
    if docs_with_exercise_name > 0:
        result = collection.update_many(
            {"exercise_name": {"$exists": True}}, {"$unset": {"exercise_name": ""}}
        )
        print(f"✅ Removed 'exercise_name' from {result.modified_count} documents")

    # Step 2: Rename userId to user_id
    if docs_with_userId > 0:
        result = collection.update_many(
            {"userId": {"$exists": True}}, {"$rename": {"userId": "user_id"}}
        )
        print(f"✅ Renamed 'userId' to 'user_id' in {result.modified_count} documents")

    # Verify
    final_count = collection.count_documents({})
    docs_with_user_id = collection.count_documents({"user_id": {"$exists": True}})
    print(
        f"✅ Migration complete. Total documents: {final_count}, with user_id: {docs_with_user_id}"
    )


def migrate_body_parts(db):
    """Rename 'userId' to 'user_id' in body_parts"""
    print("\n=== Migrating body_parts collection ===")

    collection = db.body_parts

    # Backup first
    backup_collection(db, "body_parts")

    # Rename userId to user_id
    docs_with_userId = collection.count_documents({"userId": {"$exists": True}})
    print(f"Found {docs_with_userId} documents with 'userId' field")

    if docs_with_userId > 0:
        result = collection.update_many(
            {"userId": {"$exists": True}}, {"$rename": {"userId": "user_id"}}
        )
        print(f"✅ Renamed 'userId' to 'user_id' in {result.modified_count} documents")

    # Verify
    final_count = collection.count_documents({})
    docs_with_user_id = collection.count_documents({"user_id": {"$exists": True}})
    print(
        f"✅ Migration complete. Total documents: {final_count}, with user_id: {docs_with_user_id}"
    )


def migrate_equipment(db):
    """Rename 'userId' to 'user_id' in equipment"""
    print("\n=== Migrating equipment collection ===")

    collection = db.equipment

    # Backup first
    backup_collection(db, "equipment")

    # Rename userId to user_id
    docs_with_userId = collection.count_documents({"userId": {"$exists": True}})
    print(f"Found {docs_with_userId} documents with 'userId' field")

    if docs_with_userId > 0:
        result = collection.update_many(
            {"userId": {"$exists": True}}, {"$rename": {"userId": "user_id"}}
        )
        print(f"✅ Renamed 'userId' to 'user_id' in {result.modified_count} documents")

    # Verify
    final_count = collection.count_documents({})
    docs_with_user_id = collection.count_documents({"user_id": {"$exists": True}})
    print(
        f"✅ Migration complete. Total documents: {final_count}, with user_id: {docs_with_user_id}"
    )


def migrate_hidden_items(db):
    """Rename fields in hidden_items collection to snake_case"""
    print("\n=== Migrating hidden_items collection ===")

    collection = db.hidden_items

    # Backup first
    backup_collection(db, "hidden_items")

    # Rename userId to user_id
    docs_with_userId = collection.count_documents({"userId": {"$exists": True}})
    if docs_with_userId > 0:
        result = collection.update_many(
            {"userId": {"$exists": True}}, {"$rename": {"userId": "user_id"}}
        )
        print(f"✅ Renamed 'userId' to 'user_id' in {result.modified_count} documents")

    # Rename itemType to item_type
    docs_with_itemType = collection.count_documents({"itemType": {"$exists": True}})
    if docs_with_itemType > 0:
        result = collection.update_many(
            {"itemType": {"$exists": True}}, {"$rename": {"itemType": "item_type"}}
        )
        print(
            f"✅ Renamed 'itemType' to 'item_type' in {result.modified_count} documents"
        )

    # Rename itemName to item_name
    docs_with_itemName = collection.count_documents({"itemName": {"$exists": True}})
    if docs_with_itemName > 0:
        result = collection.update_many(
            {"itemName": {"$exists": True}}, {"$rename": {"itemName": "item_name"}}
        )
        print(
            f"✅ Renamed 'itemName' to 'item_name' in {result.modified_count} documents"
        )

    # Verify
    final_count = collection.count_documents({})
    print(f"✅ Migration complete. Total documents: {final_count}")


def main():
    """Run all migrations"""
    print("🚀 Starting field name standardization migration")
    print("=" * 60)

    db = get_db()
    if db is None:
        print("❌ Failed to connect to database")
        return 1

    try:
        # Run migrations
        migrate_exercises(db)
        migrate_body_parts(db)
        migrate_equipment(db)
        migrate_hidden_items(db)

        print("\n" + "=" * 60)
        print("🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update application code to use snake_case field names")
        print("2. Test thoroughly before deploying to production")
        print("3. Backup collections are saved with timestamp suffix")

        return 0

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
