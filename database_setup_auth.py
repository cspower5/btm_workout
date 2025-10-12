"""
Clean setup script for database indexes.
This handles existing index conflicts by dropping and recreating them.
"""

from pymongo import ASCENDING
from btm_workout_db_connect import get_db


def setup_database_with_auth():
    """Setup database collections and indexes, including user authentication."""
    db = get_db()
    if db is None:
        print("❌ Cannot set up database: Connection failed.")
        return

    print("\n--- Setting up MongoDB collections and indexes (with authentication) ---")

    try:
        # 1. Exercises Collection
        try:
            db.exercises.drop_index("unique_exercise_index")
        except Exception:
            pass  # Index might not exist

        db.exercises.create_index(
            [
                ("exercise_name", ASCENDING),
                ("body_part", ASCENDING),
                ("equipment", ASCENDING),
            ],
            unique=True,
            name="unique_exercise_index",
        )
        print("✅ Index created for exercises (exercise_name, body_part, equipment).")

        # 2. Body Parts Collection
        try:
            # Drop conflicting indexes
            db.body_parts.drop_index("unique_body_part_name")
        except Exception:
            pass

        try:
            db.body_parts.drop_index("unique_body_parts_index")
        except Exception:
            pass

        db.body_parts.create_index(
            [("name", ASCENDING)], unique=True, name="unique_body_parts_index"
        )
        print("✅ Index created for body_parts (name).")

        # 3. Equipment Collection
        try:
            db.equipment.drop_index("unique_equipment_name")
        except Exception:
            pass

        db.equipment.create_index(
            [("name", ASCENDING)], unique=True, name="unique_equipment_name"
        )
        print("✅ Index created for equipment (name).")

        # 4. Users Collection - NEW for authentication
        try:
            db.users.drop_index("unique_user_email")
        except Exception:
            pass

        try:
            db.users.drop_index("unique_username")
        except Exception:
            pass

        db.users.create_index(
            [("email", ASCENDING)], unique=True, name="unique_user_email"
        )
        print("✅ Index created for users (email).")

        db.users.create_index(
            [("username", ASCENDING)], unique=True, name="unique_username"
        )
        print("✅ Index created for users (username).")

        print("--- Database setup complete! Authentication ready. ---\n")

    except Exception as e:
        print(f"❌ Database setup error: {str(e)}")


if __name__ == "__main__":
    setup_database_with_auth()
