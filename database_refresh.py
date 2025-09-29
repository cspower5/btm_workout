import requests
import os
from dotenv import load_dotenv
from btm_workout_db_connect import get_db
from pymongo.errors import BulkWriteError, DuplicateKeyError
import json 
import sys # Include sys for exiting when key is missing

# 1. Load environment variables
load_dotenv()

# --- FINAL SETUP: Use Environment Variable ---
# Note: We rely on the Render environment variable for the live key.
# This ensures security and portability.
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")


def insert_exercises_if_not_exist():
    """
    Fetches all exercises from the API and inserts them into the database,
    mapping API fields to the application's required MongoDB field names.
    """
    db = get_db()
    if db is None:
        return {"error": "Database connection is not available."}

    if not RAPIDAPI_KEY:
        # Check for key immediately before making API call
        print("Error: RAPIDAPI_KEY is missing from the environment.")
        return {"error": "API Key is missing. Cannot fetch data."}

    try:
        exercises_collection = db['exercises']
        
        # FIX: Added 'limit=0' parameter to force API to return all exercises (pagination fix)
        api_url = "https://exercisedb.p.rapidapi.com/exercises?limit=0" 
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
        }

        print("--- Attempting API Fetch from ExerciseDB ---")
        
        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses
        api_exercises = response.json()
        
        # --- FINAL CHECK: Validation ---
        if not isinstance(api_exercises, list):
            # If the response is not a list, it usually means the API is sending an error payload
            print(f"API returned non-list data: {api_exercises}")
            return {"error": "API returned unexpected data format. Check server logs."}
        # --- END FINAL CHECK ---

        inserted_count = 0
        exercises_to_insert = []

        for exercise in api_exercises:
            # --- FIX: Map ALL API field names to MongoDB field names (including 'category') ---
            mapped_exercise = {
                "body_part": exercise.get("bodyPart"),        
                "equipment": exercise.get("equipment"),
                "id": exercise.get("id"),
                "name": exercise.get("name"),
                "target": exercise.get("target"),
                "secondaryMuscles": exercise.get("secondaryMuscles"),
                "instructions": exercise.get("instructions"),
                "description": exercise.get("description"),
                "difficulty": exercise.get("difficulty"),
                "category": exercise.get("category") # <--- FINAL FIELD MAPPING FIX
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
            print(f"Successfully inserted {inserted_count} new documents.")
        else:
            print("No new exercises found to insert.")
        
        return inserted_count

    except requests.exceptions.RequestException as e:
        print(f"Error fetching exercises from API: {e}")
        return {"error": f"API Request Failed: {e}"}
    except BulkWriteError as e:
        print(f"BulkWriteError during insert: {e}")
        return {"error": "Insertion failed due to duplicate keys or invalid data."} 
    except Exception as e:
        print(f"An error occurred during database refresh: {e}")
        return {"error": f"Database Insertion Error: {e}"}