import requests
import os
from dotenv import load_dotenv
from btm_workout_db_connect import get_db
from pymongo.errors import BulkWriteError, DuplicateKeyError
import json 
import sys 

# 1. Load environment variables
load_dotenv()

# --- Use Environment Variable Directly ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") 


def insert_exercises_if_not_exist():
    """
    Fetches all exercises from the API using pagination (limit=10) and inserts them into the database.
    """
    db = get_db()
    if db is None:
        return {"error": "Database connection is not available."}

    if not RAPIDAPI_KEY:
        print("Error: RAPIDAPI_KEY is missing from the environment.")
        return {"error": "API Key is missing. Cannot fetch data."}

    # --- FIX: Initialize total_inserted_count here to prevent NameError on early crash ---
    total_inserted_count = 0
    # --- END FIX ---
    
    # --- PAGINATION SETUP ---
    limit = 10
    offset = 0
    # --- END PAGINATION SETUP ---

    try:
        exercises_collection = db['exercises']
        api_base_url = "https://exercisedb.p.rapidapi.com/exercises" 
        
        # --- API Headers ---
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY, 
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com" 
        }

        print("--- Starting Paginated API Fetch from ExerciseDB ---")
        
        while True:
            # Update parameters for the current page offset
            params = { 
                'limit': str(limit), 
                'offset': str(offset)
            } 
            
            # Execute the request
            response = requests.get(api_base_url, headers=headers, params=params)
            response.raise_for_status() # Check for 403, 404, etc.
            api_exercises = response.json()
            
            # Validation Check
            if not isinstance(api_exercises, list):
                print(f"API returned non-list data: {api_exercises}")
                return {"error": "API returned unexpected data format."}

            if not api_exercises:
                print("Pagination complete or no data received.")
                break # Exit loop if no exercises are returned

            exercises_to_insert = []

            for exercise in api_exercises:
                # Check for required fields before mapping
                if not exercise.get("name") or not exercise.get("bodyPart"):
                    continue

                # --- MAPPING: Ensure correct structure for MongoDB insertion ---
                mapped_exercise = {
                    "body_part": exercise.get("bodyPart"),        
                    "equipment": exercise.get("equipment"),
                    "id": exercise.get("id"),                     
                    "exercise_name": exercise.get("name"),        
                    "target": exercise.get("target"),
                    "secondaryMuscles": exercise.get("secondaryMuscles"),
                    "instructions": exercise.get("instructions"),
                    "description": exercise.get("description"),
                    "difficulty": exercise.get("difficulty"),
                    "category": exercise.get("category")
                }

                # Check for duplicates before insertion
                existing_exercise = exercises_collection.find_one({
                    "id": mapped_exercise["id"]
                })

                if not existing_exercise:
                    exercises_to_insert.append(mapped_exercise)
            
            if exercises_to_insert:
                # Insert documents for the current batch
                result = exercises_collection.insert_many(exercises_to_insert, ordered=False)
                total_inserted_count += len(result.inserted_ids)
                print(f"Batch inserted {len(result.inserted_ids)} new documents. Total: {total_inserted_count}")
            
            # Update offset for the next page
            offset += limit
            
            # If the current batch was smaller than the limit, we've reached the end
            if len(api_exercises) < limit:
                break


        print(f"--- Pagination finished. Total documents inserted: {total_inserted_count} ---")
        return total_inserted_count

    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
             print(f"API Request Failed: Status {e.response.status_code}")
             return {"error": f"API Request Failed: Status {e.response.status_code}. Check key/host."}
        else:
             print(f"Network Error: {e}")
             return {"error": f"Network Error during API fetch: {e}"}
    except BulkWriteError as e:
        # If a BulkWriteError occurs, the thread should not crash. We return the count 
        # of items successfully inserted up to that point.
        print(f"BulkWriteError during insert: {e}")
        return total_inserted_count # Return the count accumulated before the write error
    except Exception as e:
        print(f"An error occurred during database refresh: {e}")
        return {"error": f"Database Insertion Error: {e}"}
