from pymongo import ASCENDING
from btm_workout_db_connect import get_db


def create_initial_collections_and_indexes():
    """Creates collections and unique indexes for data integrity."""
    db = get_db()
    if db is None:
        print("❌ Cannot set up database: Connection failed.")
        return

    print("\n--- Setting up MongoDB collections and indexes ---")

    # Drop old index if exists
    try:
        db.exercises.drop_index("unique_exercise_index")
        print("Dropped old exercises index: unique_exercise_index")
    except Exception as e:
        print(f"No old exercises index to drop or error: {e}")
    # Create compound unique index on (exercise_name, body_part, equipment, user_id)
    db.exercises.create_index(
        [
            ("exercise_name", ASCENDING),
            ("body_part", ASCENDING),
            ("equipment", ASCENDING),
            ("user_id", ASCENDING),
        ],
        unique=True,
        name="unique_exercise_index",
    )
    print(
        "✅ Index created for exercises (exercise_name, body_part, equipment, user_id)."
    )

    # Drop old index if exists
    try:
        db.body_parts.drop_index("unique_body_parts_index")
        print("Dropped old body_parts index: unique_body_parts_index")
    except Exception as e:
        print(f"No old body_parts index to drop or error: {e}")
    db.body_parts.create_index(
        [("name", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="unique_body_parts_index",
    )
    print("✅ Index created for body_parts (name, user_id) as unique_body_parts_index.")

    # Drop old index if exists
    try:
        db.equipment.drop_index("unique_equipment_name")
        print("Dropped old equipment index: unique_equipment_name")
    except Exception as e:
        print(f"No old equipment index to drop or error: {e}")
    db.equipment.create_index(
        [("name", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="unique_equipment_name",
    )
    print("✅ Index created for equipment (name, user_id).")

    # 4. Users Collection - Unique indexes for authentication
    db.users.create_index([("email", ASCENDING)], unique=True, name="unique_user_email")
    print("✅ Index created for users (email).")

    db.users.create_index(
        [("username", ASCENDING)], unique=True, name="unique_username"
    )
    print("✅ Index created for users (username).")

    # 5. Difficulties Collection - No unique index needed, simple list.
    print("--- Setup complete ---\n")


if __name__ == "__main__":
    create_initial_collections_and_indexes()
