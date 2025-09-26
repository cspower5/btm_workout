import requests
import os
from dotenv import load_dotenv
from btm_workout_db_connect import get_db
from pymongo.errors import BulkWriteError, DuplicateKeyError

# 1. Load environment variables
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not RAPIDAPI_KEY:
    print("Error: The RAPIDAPI_KEY environment variable is missing.")

def insert_exercises_if_not_exist():
    """
    Fetches all exercises from the API and inserts them into the database,
    mapping API fields to the application's required MongoDB field names.
    """
    db = get_db()
    if db is None:
        return {"error": "Database connection is not available."}

    if not RAPIDAPI_KEY:
        return {"error": "API Key is missing. Cannot fetch data."}

    try:
        exercises_collection = db['exercises']
        
        api_url = "https://exercisedb.p.rapidapi.com/exercises"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
        }

        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses
        api_exercises = response.json()

        inserted_count = 0
        exercises_to_insert = []

        for exercise in api_exercises:
            # --- FIX: Map API field names to MongoDB field names ---
            mapped_exercise = {
                "exercise_name": exercise.get("name"),    # Maps 'name' to 'exercise_name'
                "body_part": exercise.get("bodyPart"),    # Maps 'bodyPart' to 'body_part'
                "equipment": exercise.get("equipment"),
                "target": exercise.get("target"),
                "gifUrl": exercise.get("gifUrl"),
                "secondaryMuscles": exercise.get("secondaryMuscles"),
                "instructions": exercise.get("instructions"),
                "description": exercise.get("description"),
                "difficulty": exercise.get("difficulty")
            }

            # Check if an exercise with the same mapped fields already exists
            existing_exercise = exercises_collection.find_one({
                "exercise_name": mapped_exercise["exercise_name"],
                "body_part": mapped_exercise["body_part"],
                "equipment": mapped_exercise["equipment"]
            })

            if not existing_exercise:
                exercises_to_insert.append(mapped_exercise)
        
        if exercises_to_insert:
            # Insert all exercises in one batch for performance
            result = exercises_collection.insert_many(exercises_to_insert, ordered=False)
            inserted_count = len(result.inserted_ids)
        
        return inserted_count

    except requests.exceptions.RequestException as e:
        print(f"Error fetching exercises from API: {e}")
        return {"error": f"API Request Failed: {e}"}
    except BulkWriteError as e:
        print(f"BulkWriteError during insert: {e}")
        # Returns the count of exercises inserted before the failure
        return len(e.details.get('insertedIds', [])) 
    except Exception as e:
        print(f"An error occurred during database refresh: {e}")
        return {"error": f"Database Insertion Error: {e}"}

# Note: The if __name__ == '__main__': block is removed to prevent
# this file from running automatically when imported by flask_server.py
