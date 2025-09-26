import requests
import os
from dotenv import load_dotenv
from btm_workout_db_connect import get_db
from pymongo.errors import BulkWriteError, DuplicateKeyError
import json 

# 1. Load environment variables
load_dotenv()

# --- FIX: TEMPORARILY HARDCODE KEY FOR FINAL DEBUGGING ---
# REPLACE "YOUR_ACTUAL_RAPIDAPI_KEY_HERE" with the full, correct key string
RAPIDAPI_KEY = "YOUR_ACTUAL_RAPIDAPI_KEY_HERE" # <-- PASTE YOUR KEY HERE
# --- END TEMPORARY FIX ---


def insert_exercises_if_not_exist():
    """
    Fetches all exercises from the API and inserts them into the database,
    mapping API fields to the application's required MongoDB field names.
    """
    db = get_db()
    if db is None:
        return {"error": "Database connection is not available."}

    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "YOUR_ACTUAL_RAPIDAPI_KEY_HERE":
        return {"error": "API Key is missing or default. Cannot fetch data."}

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
        response.raise_for_status() # Must be 200 OK
        api_exercises = response.json()
        
        # --- NEW DEBUGGING LOGGING ---
        # Log the response content to see what the API actually sent back
        print(f"API RESPONSE STATUS: {response.status_code}")
        print(f"API RESPONSE ITEMS RECEIVED: {len(api_exercises) if isinstance(api_exercises, list) else 'Non-list data'}")
        print(f"API RAW RESPONSE HEAD: {json.dumps(api_exercises)[:200]}")
        # --- END DEBUGGING LOGGING ---


        # --- FINAL CHECK: Validation ---
        if not isinstance(api_exercises, list):
            # The API returned an unexpected payload (not the list of exercises)
            return {"error": "API returned unexpected data format. Check server logs."}
        # --- END FINAL CHECK ---

        inserted_count = 0
        exercises_to_insert = []

        for exercise in api_exercises:
            # --- Map API field names to MongoDB field names (final structure) ---
            mapped_exercise = {
                "exercise_name": exercise.get("name"),    
                "body_part": exercise.get("bodyPart"),    
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