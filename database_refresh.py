import requests
import os
from dotenv import load_dotenv
from btm_workout_db_connect import get_db
from pymongo.errors import BulkWriteError, DuplicateKeyError
import json 
import sys 

# 1. Load environment variables
load_dotenv()

# --- FIX: Use Environment Variable Directly ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") 


def insert_exercises_if_not_exist():
    """
    Fetches a single exercise from the API for diagnostic purposes.
    If successful, it inserts the single exercise into the database.
    """
    db = get_db()
    if db is None:
        return {"error": "Database connection is not available."}

    if not RAPIDAPI_KEY:
        print("Error: RAPIDAPI_KEY is missing from the environment.")
        return {"error": "API Key is missing. Cannot fetch data."}

    try:
        exercises_collection = db['exercises']
        
        # --- FINAL DIAGNOSTIC: Fetching ONLY one exercise (Test Authentication) ---
        api_url = "https://exercisedb.p.rapidapi.com/exercises/0001" 
        
        # NOTE: We only send the Host header for this basic diagnostic test.
        headers = {
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
        }

        print("--- Attempting API Fetch (Diagnostic Single Item) ---")
        
        # Execute the request
        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # Raise an HTTPError for non-200 status
        api_exercise = response.json()
        
        # --- CRITICAL CHECK: Does the API send back a single dictionary? ---
        if isinstance(api_exercise, dict) and 'name' in api_exercise:
            
            # If we succeed, insert the single exercise and return a count of 1.
            exercises_to_insert = [{
                "body_part": api_exercise.get("bodyPart"),        
                "equipment": api_exercise.get("equipment"),
                "id": api_exercise.get("id"),                     
                "exercise_name": api_exercise.get("name"),        
                "target": api_exercise.get("target"),
                "secondaryMuscles": api_exercise.get("secondaryMuscles"),
                "instructions": api_exercise.get("instructions"),
                "description": api_exercise.get("description"),
                "difficulty": api_exercise.get("difficulty"),
                "category": api_exercise.get("category")
            }]
            
            # Clean collection first to prevent unique index error on single insert
            exercises_collection.delete_many({}) 
            
            result = exercises_collection.insert_many(exercises_to_insert, ordered=False)
            inserted_count = len(result.inserted_ids)
            print(f"SUCCESS: Inserted {inserted_count} single diagnostic document.")
            
            # Since we inserted ONE, we return 1.
            return 1 

        else:
            print(f"FAILURE: API returned unexpected data format for single item: {api_exercise}")
            return {"error": "API is blocking single-item access or key is wrong."}

    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
             print(f"API Request Failed: Status {e.response.status_code}")
             return {"error": f"API Request Failed: Status {e.response.status_code}. Check key/host."}
        else:
             print(f"Network Error: {e}")
             return {"error": f"Network Error during API fetch: {e}"}
    except BulkWriteError as e:
        print(f"BulkWriteError during insert: {e}")
        return {"error": "Insertion failed due to duplicate keys or invalid data."} 
    except Exception as e:
        print(f"An error occurred during database refresh: {e}")
        return {"error": f"Database Insertion Error: {e}"}
