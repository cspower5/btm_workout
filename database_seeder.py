import sys
from btm_workout_db_connect import get_db


def seed_database():
    db = get_db()
    if db is None:
        print("❌ Error: Could not connect to the database. Check your .env MONGO_URI.")
        sys.exit(1)

    print("Seeding database with initial data...")

    # Seed a sample user
    user_id = db.users.insert_one(
        {
            "username": "seeduser",
            "email": "seeduser@example.com",
            "password": "hashedpassword",
            "first_name": "Seed",
            "last_name": "User",
        }
    ).inserted_id

    # Sample Body Parts (with user_id)
    body_parts_data = [
        {"name": "Chest", "user_id": user_id},
        {"name": "Back", "user_id": user_id},
        {"name": "Legs", "user_id": user_id},
        {"name": "Shoulders", "user_id": user_id},
        {"name": "Arms", "user_id": user_id},
        {"name": "Core", "user_id": user_id},
    ]
    db.body_parts.delete_many({})
    db.body_parts.insert_many(body_parts_data)

    # Sample Equipment (with user_id)
    equipment_data = [
        {"name": "Dumbbell", "user_id": user_id},
        {"name": "Barbell", "user_id": user_id},
        {"name": "Kettlebell", "user_id": user_id},
        {"name": "Body Weight", "user_id": user_id},
        {"name": "Cable", "user_id": user_id},
    ]
    db.equipment.delete_many({})
    db.equipment.insert_many(equipment_data)

    # Sample Difficulties (You'll need a way to insert these unique values)
    # NOTE: Assuming difficulty levels are used for filtering/dropdowns

    # Sample Exercises (with user_id)
    exercises_data = [
        {
            "exercise_name": "Barbell Bench Press",
            "body_part": "Chest",
            "equipment": "Barbell",
            "target": "Pectorals",
            "reps": "8-12",
            "sets": "3",
            "instructions": [
                "Lie on a bench.",
                "Lower the bar to your chest.",
                "Push the bar back up.",
            ],
            "difficulty": "Intermediate",
            "user_id": user_id,
        },
        {
            "exercise_name": "Dumbbell Curl",
            "body_part": "Arms",
            "equipment": "Dumbbell",
            "target": "Biceps",
            "reps": "10-15",
            "sets": "3",
            "instructions": [
                "Hold a dumbbell in each hand.",
                "Curl the dumbbells up.",
                "Lower them slowly.",
            ],
            "difficulty": "Beginner",
            "user_id": user_id,
        },
        {
            "exercise_name": "Squat",
            "body_part": "Legs",
            "equipment": "Body Weight",
            "target": "Quadriceps",
            "reps": "15-20",
            "sets": "3",
            "instructions": [
                "Stand with feet shoulder-width apart.",
                "Lower your hips as if sitting.",
                "Push back up to starting position.",
            ],
            "difficulty": "Beginner",
            "user_id": user_id,
        },
    ]
    db.exercises.delete_many({})
    db.exercises.insert_many(exercises_data)

    print("✅ Database seeding complete! Check your live app.")


if __name__ == "__main__":
    seed_database()
