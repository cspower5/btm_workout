"""
User helper functions for development and debugging.
Makes it easier to work with ObjectId-based user relationships.
"""

import btm_workout_db_connect as db_connect
from bson import ObjectId


def get_user_id_by_username(username):
    """Get ObjectId for a username"""
    db = db_connect.get_db()
    user = db.users.find_one({"username": username})
    return str(user["_id"]) if user else None


def get_username_by_user_id(user_id):
    """Get username for an ObjectId"""
    db = db_connect.get_db()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    return user.get("username") if user else None


def get_exercises_by_username(username):
    """Get all exercises for a username (for debugging)"""
    user_id = get_user_id_by_username(username)
    if not user_id:
        return []

    db = db_connect.get_db()
    exercises = list(db.exercises.find({"userId": user_id}))

    # Add username to each exercise for readability
    for exercise in exercises:
        exercise["_username"] = username

    return exercises


def show_user_data_summary():
    """Print a summary of all users and their data"""
    db = db_connect.get_db()

    print("=== USER DATA SUMMARY ===")
    users = list(db.users.find({}, {"username": 1, "email": 1}))

    for user in users:
        user_id = str(user["_id"])
        username = user["username"]
        email = user["email"]

        # Count user's data
        exercise_count = db.exercises.count_documents({"userId": user_id})
        body_part_count = db.body_parts.count_documents({"userId": user_id})
        equipment_count = db.equipment.count_documents({"userId": user_id})

        print(f"\nUser: {username} ({email})")
        print(f"  ID: {user_id}")
        print(f"  Exercises: {exercise_count}")
        print(f"  Body Parts: {body_part_count}")
        print(f"  Equipment: {equipment_count}")


if __name__ == "__main__":
    # Example usage
    print("Example: Finding que's exercises...")
    que_exercises = get_exercises_by_username("que")
    for ex in que_exercises:
        print(f"  {ex.get('exercise_name')} (ID: {ex.get('_id')})")

    print("\nFull summary:")
    show_user_data_summary()
