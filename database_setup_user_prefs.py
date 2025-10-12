#!/usr/bin/env python3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Setup user_hidden_items collection for user customization features
"""


def setup_user_preferences_collection():
    """Create indexes for user_hidden_items collection"""

    from btm_workout_db_connect import get_db

    db = get_db()

    print("🔧 Setting up user_hidden_items collection...")

    # Create the collection (will be created automatically on first insert)
    collection = db.user_hidden_items

    # Create indexes for efficient querying
    indexes_to_create = [
        # Index for finding user's hidden items by collection type
        (
            [("userId", 1), ("collection", 1)],
            {"name": "user_collection_index", "unique": True},
        ),
        # Index for just userId lookups
        ([("userId", 1)], {"name": "user_index"}),
    ]

    for index_spec, options in indexes_to_create:
        try:
            collection.create_index(index_spec, **options)
            print(f"✅ Created index: {options['name']}")
        except Exception as e:
            print(f"ℹ️ Index {options['name']} already exists or error: {e}")

    print("✅ User preferences collection setup complete!")


def main():
    """Setup user preferences collection"""
    print("🚀 Setting up user customization features...")

    try:
        setup_user_preferences_collection()
        print("\n🎉 Setup completed successfully!")
        print("\nUsers can now:")
        print("- Hide exercises they don't want to see")
        print("- Hide body parts they don't train")
        print("- Hide equipment they don't have access to")
        print("- Add their own custom exercises/body parts/equipment")
        print("- Restore hidden items anytime")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
