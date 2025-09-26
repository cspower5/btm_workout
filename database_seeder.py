import sys
from btm_workout_db_connect import get_db

def seed_database():
    db = get_db()
    if db is None:
        print("❌ Error: Could not connect to the database. Check your .env MONGO_URI.")
        sys.exit(1)
        
    print("Seeding database with initial data...")

    # Sample Body Parts
    body_parts_data = [
        {"name": "Chest"},
        {"name": "Back"},
        {"name": "Legs"},
        {"name": "Shoulders"},
        {"name": "Arms"},
        {"name": "Core"},
    ]
    # Delete existing data before seeding to ensure a clean slate
    db.body_parts.delete_many({})
    db.body_parts.insert_many(body_parts_data)
    
    # Sample Equipment
    equipment_data = [
        {"name": "Dumbbell"},
        {"name": "Barbell"},
        {"name": "Kettlebell"},
        {"name": "Body Weight"},
        {"name": "Cable"},
    ]
    db.equipment.delete_many({})
    db.equipment.insert_many(equipment_data)
    
    # Sample Difficulties (You'll need a way to insert these unique values)
    # NOTE: Assuming difficulty levels are used for filtering/dropdowns
    
    # Sample Exercises
    exercises_data = [
        {
            "name": "Barbell Bench Press",
            "bodyPart": "Chest",
            "equipment": "Barbell",
            "target": "Pectorals",
            "reps": "8-12",
            "sets": "3",
            "instructions": ["Lie on a bench.", "Lower the bar to your chest.", "Push the bar back up."],
            "difficulty": "Intermediate",
        },
        {
            "name": "Dumbbell Curl",
            "bodyPart": "Arms",
            "equipment": "Dumbbell",
            "target": "Biceps",
            "reps": "10-15",
            "sets": "3",
            "instructions": ["Hold a dumbbell in each hand.", "Curl the dumbbells up.", "Lower them slowly."],
            "difficulty": "Beginner",
        },
        {
            "name": "Squat",
            "bodyPart": "Legs",
            "equipment": "Body Weight",
            "target": "Quadriceps",
            "reps": "15-20",
            "sets": "3",
            "instructions": ["Stand with feet shoulder-width apart.", "Lower your hips as if sitting.", "Push back up to starting position."],
            "difficulty": "Beginner",
        },
    ]
    db.exercises.delete_many({})
    db.exercises.insert_many(exercises_data)
    
    print("✅ Database seeding complete! Check your live app.")

if __name__ == "__main__":
    seed_database()
