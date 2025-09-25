from pymongo import ASCENDING
from btm_workout_db_connect import get_db

def create_initial_collections_and_indexes():
    """Creates collections and unique indexes for data integrity."""
    db = get_db()
    if db is None:
        print("❌ Cannot set up database: Connection failed.")
        return

    print("\n--- Setting up MongoDB collections and indexes ---")

    # 1. Exercises Collection - Unique index on the primary definition fields
    db.exercises.create_index(
        [
            ("name", ASCENDING),
            ("bodyPart", ASCENDING),
            ("equipment", ASCENDING)
        ],
        unique=True,
        name="unique_exercise_index"
    )
    print("✅ Index created for exercises (name, bodyPart, equipment).")

    # 2. Body Parts Collection - Unique index on name
    db.body_parts.create_index(
        [("name", ASCENDING)],
        unique=True,
        name="unique_body_part_name"
    )
    print("✅ Index created for body_parts (name).")

    # 3. Equipment Collection - Unique index on name
    db.equipment.create_index(
        [("name", ASCENDING)],
        unique=True,
        name="unique_equipment_name"
    )
    print("✅ Index created for equipment (name).")

    # 4. Difficulties Collection - No unique index needed, simple list.
    print("--- Setup complete ---\n")

if __name__ == "__main__":
    create_initial_collections_and_indexes()
