from pymongo import ASCENDING
from btm_workout_db_connect import get_db


def create_initial_collections_and_indexes():
    """Creates collections and unique indexes for data integrity."""
    db = get_db()
    if db is None:
        print("❌ Cannot set up database: Connection failed.")
        return

    print("\n--- Setting up MongoDB collections and indexes ---")

    # 1. Exercises Collection
    # Drop old indexes if they exist
    try:
        db.exercises.drop_index("unique_exercise_index")
        print("Dropped old exercises index: unique_exercise_index")
    except Exception as e:
        print(f"No old exercises index to drop or error: {e}")

    try:
        db.exercises.drop_index("unique_app_index")
        print("Dropped old exercises index: unique_app_index")
    except Exception as e:
        print(f"No old unique_app_index to drop or error: {e}")

    # Create compound unique index on (name, body_part, equipment, user_id)
    # MUST match Atlas: unique_exercises_index using 'name' (not exercise_name) and 'user_id'
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
    print(
        "✅ Index created for exercises (name, body_part, equipment, user_id) as unique_exercises_index."
    )

    # 2. Body Parts Collection
    # Drop old index if exists
    try:
        db.body_parts.drop_index("unique_body_parts_index")
        print("Dropped old body_parts index: unique_body_parts_index")
    except Exception as e:
        print(f"No old body_parts index to drop or error: {e}")

    # Create compound unique index on (name, user_id)
    # MUST match Atlas: unique_body_part_index (singular)
    db.body_parts.create_index(
        [("name", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="unique_body_part_index",
    )
    print("✅ Index created for body_parts (name, user_id) as unique_body_part_index.")

    # 3. Equipment Collection
    # Drop old index if exists
    try:
        db.equipment.drop_index("unique_equipment_name")
        print("Dropped old equipment index: unique_equipment_name")
    except Exception as e:
        print(f"No old equipment index to drop or error: {e}")

    # Create compound unique index on (name, user_id)
    # MUST match Atlas: unique_equipment_index
    db.equipment.create_index(
        [("name", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="unique_equipment_index",
    )
    print("✅ Index created for equipment (name, user_id) as unique_equipment_index.")

    # 4. Users Collection
    # Drop old indexes if they exist
    try:
        db.users.drop_index("unique_user_email")
        print("Dropped old users index: unique_user_email")
    except Exception as e:
        print(f"No old users index to drop or error: {e}")

    try:
        db.users.drop_index("unique_username")
        print("Dropped old users index: unique_username")
    except Exception as e:
        print(f"No old users index to drop or error: {e}")

    # Create unique index on email only
    # MUST match Atlas: unique_users_index (only email, no username index in Atlas)
    db.users.create_index(
        [("email", ASCENDING)], unique=True, name="unique_users_index"
    )
    print("✅ Index created for users (email) as unique_users_index.")

    # 5. Hidden Items Collection - Track items users want to hide from their view
    # Using snake_case to match other field names: user_id, item_type, item_name
    db.hidden_items.create_index(
        [("user_id", ASCENDING), ("item_type", ASCENDING), ("item_name", ASCENDING)],
        unique=True,
        name="unique_hidden_item",
    )
    print("✅ Index created for hidden_items (user_id, item_type, item_name).")

    print("--- Setup complete ---\n")


if __name__ == "__main__":
    create_initial_collections_and_indexes()
