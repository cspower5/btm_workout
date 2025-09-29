import requests
import os
from dotenv import load_dotenv
from btm_workout_db_connect import get_db
from pymongo.errors import BulkWriteError, DuplicateKeyError
import json 
import sys 
# Import sys for writing debug messages directly to standard error stream
# This forces logs to appear in Gunicorn/Render logs.

# 1. Load environment variables
load_dotenv()

# --- FIX: Use Environment Variable Directly ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") 

# Helper function to write logs directly to the Gunicorn log stream (sys.stderr)
# This bypasses Gunicorn's suppression of standard print() statements.
def log_debug(message):
    sys.stderr.write(f"[REFRESH DEBUG] {message}\n")


def insert_exercises_if_not_exist():
    """
    Fetches all exercises from the API and inserts them into the database.
    """
    db = get_db()
    if db is None:
        return {"error": "Database connection is not available."}

    if not RAPIDAPI_KEY:
        log_debug("Error: RAPIDAPI_KEY is missing from the environment.")
        return {"error": "API Key is missing. Cannot fetch data."}

    try:
        # --- FIX: Changed collection name from 'exercise' to 'exercises' ---
        exercises_collection = db['exercises']
        
        # --- FINAL FIX: Use Python requests 'params' and 'headers' argument directly ---
        # NOTE: RapidAPI sometimes requires the key in the params for full access.
        api_url = "https://exercisedb.p.rapidapi.com/exercises" 
        
        # We pass both the pagination limit AND the key as parameters
        params = { 
            'limit': '0', 
            'x-rapidapi-key': RAPIDAPI_KEY  # <-- Passed as a URL parameter
        } 
        
        headers = {
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com" # Host Check remains
        }

        log_debug("--- Attempting API Fetch from ExerciseDB ---")
        
        # Execute the request with explicit headers and parameters
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status() # Raise an HTTPError for non-200 status
        api_exercises = response.json()
        
        # --- NEW DEBUGGING LOGGING ---
        log_debug(f"API Response Status: {response.status_code}")
        if isinstance(api_exercises, list):
            log_debug(f"Items Received: {len(api_exercises)}")
            log_debug(f"Raw Data Head: {json.dumps(api_exercises)[:500]}...")
        else:
            log_debug(f"Raw Data Head (Non-list): {json.dumps(api_exercises)[:500]}")
        # --- END DEBUGGING LOGGING ---
        
        
        # Validation Check
        if not isinstance(api_exercises, list):
            log_debug(f"API returned non-list data: {api_exercises}")
            return {"error": "API returned unexpected data format."}

        inserted_count = 0
        exercises_to_insert = []

        for exercise in api_exercises:
            # Check for name/body_part presence before insertion logic
            if not exercise.get("name") or not exercise.get("bodyPart"):
                continue

            # --- CRITICAL FIX: The 10-field mapping ---
            mapped_exercise = {
                "body_part": exercise.get("bodyPart"),        # Application key
                "equipment": exercise.get("equipment"),
                "id": exercise.get("id"),                     # Renamed key from 'api_id'
                "exercise_name": exercise.get("name"),        # Application key
                "target": exercise.get("target"),
                "secondaryMuscles": exercise.get("secondaryMuscles"),
                "instructions": exercise.get("instructions"),
                "description": exercise.get("description"),
                "difficulty": exercise.get("difficulty"),
                "category": exercise.get("category")
            }
            # --- END CRITICAL FIX ---


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
            log_debug(f"Successfully inserted {inserted_count} new documents.")
        else:
            log_debug("No new exercises found to insert.")
        
        return inserted_count

    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
             log_debug(f"API Request Failed: Status {e.response.status_code}")
             return {"error": f"API Request Failed: Status {e.response.status_code}. Check key/host."}
        else:
             log_debug(f"Network Error: {e}")
             return {"error": f"Network Error during API fetch: {e}"}
    except BulkWriteError as e:
        log_debug(f"BulkWriteError during insert: {e}")
        return {"error": "Insertion failed due to duplicate keys or invalid data."} 
    except Exception as e:
        log_debug(f"An error occurred during database refresh: {e}")
        return {"error": f"Database Insertion Error: {e}"}