from btm_workout_db_connect import db

def get_body_parts():
    if db is None:
        print("Database connection is not available.")
        return []

    try:
        exercises_collection = db['exercises']
        body_parts = exercises_collection.distinct("bodyPart")
        return body_parts
    except Exception as e:
        print(f"An error occurred while fetching body parts: {e}")
        return []

if __name__ == '__main__':
    # This block allows you to run the file independently for testing
    # but it won't be executed when imported by flask_server.py
    # This is a good practice for modular code.
    print("Testing get_body_parts() function:")
    parts = get_body_parts()
    print(parts)
