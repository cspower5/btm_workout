#!/usr/bin/env python3
# ruff: noqa: E402
import os
import sys
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from btm_workout_db_connect import get_db


def backup_collections():
    """Create backups before migration"""
    db = get_db()
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    backup_dir = f"db_backups/userid_migration_{timestamp}"

    os.makedirs(backup_dir, exist_ok=True)

    collections = ["exercises", "body_parts", "equipment"]

    for collection_name in collections:
        collection = db[collection_name]
        documents = list(collection.find({}))

        # Remove ObjectId for JSON serialization
        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        backup_file = f"{backup_dir}/{collection_name}_backup.json"
        with open(backup_file, "w") as f:
            json.dump(documents, f, indent=2, default=str)

        print(
            f"✅ Backed up {len(documents)} documents from {collection_name} to {backup_file}"
        )

    return backup_dir


def add_optional_userid_field():
    """Add optional userId field to existing documents"""
    db = get_db()
    collections = ["exercises", "body_parts", "equipment"]

    for collection_name in collections:
        collection = db[collection_name]

        # Count documents without userId field
        count_without_userid = collection.count_documents(
            {"userId": {"$exists": False}}
        )

        if count_without_userid > 0:
            print(
                f"📝 Adding optional userId field to {count_without_userid} documents in {collection_name}"
            )

            # Add userId: null to documents that don't have it
            # This makes them "public" or "legacy" data that all users can see
            result = collection.update_many(
                {"userId": {"$exists": False}}, {"$set": {"userId": None}}
            )

            print(f"✅ Updated {result.modified_count} documents in {collection_name}")
        else:
            print(f"✅ All documents in {collection_name} already have userId field")


def verify_migration():
    """Verify the migration was successful"""
    db = get_db()
    collections = ["exercises", "body_parts", "equipment"]

    print("\n🔍 Verifying migration...")

    for collection_name in collections:
        collection = db[collection_name]

        total_docs = collection.count_documents({})
        docs_with_userid = collection.count_documents({"userId": {"$exists": True}})
        docs_with_null_userid = collection.count_documents({"userId": None})

        print(f"📊 {collection_name}:")
        print(f"   Total documents: {total_docs}")
        print(f"   Documents with userId field: {docs_with_userid}")
        print(f"   Documents with userId=null (legacy): {docs_with_null_userid}")

        if total_docs != docs_with_userid:
            print(
                f"⚠️  WARNING: Some documents in {collection_name} don't have userId field!"
            )
            return False

    print("✅ Migration verification successful!")
    return True


def create_indexes_for_userid():
    """Create indexes that support both legacy and user-specific queries"""
    db = get_db()
    collections = ["exercises", "body_parts", "equipment"]

    print("\n🔧 Creating userId indexes...")

    for collection_name in collections:
        collection = db[collection_name]

        # Create sparse index on userId (allows null values)
        index_name = f"{collection_name}_userId_sparse"
        collection.create_index([("userId", 1)], sparse=True, name=index_name)
        print(f"✅ Created sparse index {index_name}")

        # Create compound indexes for efficient queries
        if collection_name == "exercises":
            # For exercise queries by body part and user
            collection.create_index(
                [("userId", 1), ("body_part", 1)],
                name=f"{collection_name}_userId_bodypart",
            )
            # For exercise queries by equipment and user
            collection.create_index(
                [("userId", 1), ("equipment", 1)],
                name=f"{collection_name}_userId_equipment",
            )


def main():
    """Run the migration"""
    print("🚀 Starting userId field migration...")
    print("This migration adds optional userId fields to existing collections.")
    print("It's backward compatible and won't break existing functionality.\n")

    try:
        # Step 1: Create backups
        print("📦 Creating backups...")
        backup_dir = backup_collections()
        print(f"✅ Backups created in: {backup_dir}\n")

        # Step 2: Add optional userId field
        print("📝 Adding optional userId field...")
        add_optional_userid_field()
        print()

        # Step 3: Create indexes
        create_indexes_for_userid()
        print()

        # Step 4: Verify migration
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("\nNext steps:")
            print("1. Deploy the updated API endpoints that handle userId")
            print("2. Test with both legacy data (userId=null) and new user data")
            print("3. Monitor for any issues")
            print(f"4. Backups available in: {backup_dir}")
        else:
            print("\n❌ Migration verification failed!")
            return 1

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(
            f"📦 Restore from backups in: {backup_dir if 'backup_dir' in locals() else 'db_backups/'}"
        )
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
