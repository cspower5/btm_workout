#!/usr/bin/env python3
# ruff: noqa: E402
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from btm_workout_db_connect import get_db


def rollback_userid_field():
    """Remove userId field from all documents"""
    db = get_db()
    collections = ["exercises", "body_parts", "equipment"]

    print("🔄 Rolling back userId field changes...")

    for collection_name in collections:
        collection = db[collection_name]

        # Count documents with userId field
        count_with_userid = collection.count_documents({"userId": {"$exists": True}})

        if count_with_userid > 0:
            print(
                f"📝 Removing userId field from {count_with_userid} documents in {collection_name}"
            )

            # Remove userId field from all documents
            result = collection.update_many(
                {"userId": {"$exists": True}}, {"$unset": {"userId": ""}}
            )

            print(f"✅ Updated {result.modified_count} documents in {collection_name}")
        else:
            print(f"✅ No userId fields found in {collection_name}")


def remove_userid_indexes():
    """Remove userId indexes that were created during migration"""
    db = get_db()
    collections = ["exercises", "body_parts", "equipment"]

    print("\n🗑️ Removing userId indexes...")

    for collection_name in collections:
        collection = db[collection_name]

        try:
            # Remove the sparse userId index
            collection.drop_index(f"{collection_name}_userId_sparse")
            print(f"✅ Dropped index {collection_name}_userId_sparse")
        except Exception:
            print(
                f"ℹ️ Index {collection_name}_userId_sparse not found or already dropped"
            )

        # Remove compound indexes for exercises
        if collection_name == "exercises":
            try:
                collection.drop_index(f"{collection_name}_userId_bodypart")
                print(f"✅ Dropped index {collection_name}_userId_bodypart")
            except Exception:
                print(f"ℹ️ Index {collection_name}_userId_bodypart not found")

            try:
                collection.drop_index(f"{collection_name}_userId_equipment")
                print(f"✅ Dropped index {collection_name}_userId_equipment")
            except Exception:
                print(f"ℹ️ Index {collection_name}_userId_equipment not found")


def verify_rollback():
    """Verify the rollback was successful"""
    db = get_db()
    collections = ["exercises", "body_parts", "equipment"]

    print("\n🔍 Verifying rollback...")

    for collection_name in collections:
        collection = db[collection_name]

        total_docs = collection.count_documents({})
        docs_with_userid = collection.count_documents({"userId": {"$exists": True}})

        print(f"📊 {collection_name}:")
        print(f"   Total documents: {total_docs}")
        print(f"   Documents with userId field: {docs_with_userid}")

        if docs_with_userid > 0:
            print(
                f"⚠️  WARNING: Some documents in {collection_name} still have userId field!"
            )
            return False

    print("✅ Rollback verification successful! All userId fields removed.")
    return True


def main():
    """Run the rollback"""
    print("🚀 Starting Atlas database rollback...")
    print("This will remove userId fields from Atlas to restore production state.")

    # Confirm we're connecting to Atlas
    print("Connected to database. Please confirm this is Atlas before proceeding.\n")

    # Ask for confirmation
    response = input(
        "⚠️ Are you sure you want to rollback Atlas database? (type 'yes' to confirm): "
    )

    if response.lower() != "yes":
        print("❌ Rollback cancelled.")
        return 1

    try:
        # Step 1: Remove userId fields
        rollback_userid_field()

        # Step 2: Remove indexes
        remove_userid_indexes()

        # Step 3: Verify rollback
        if verify_rollback():
            print("\n🎉 Atlas rollback completed successfully!")
            print("Production app should now work normally.")
        else:
            print("\n❌ Rollback verification failed!")
            return 1

    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
