import requests
import os
from dotenv import load_dotenv
from btm_workout_db_connect import get_db
from pymongo.errors import BulkWriteError, DuplicateKeyError
from pymongo import ASCENDING
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

    # --- PAGINATION SETUP ---
    total_inserted_count = 0
    limit = 10
    offset = 0
    # --- END PAGINATION SETUP ---

    try:
        # --- CRITICAL PERSISTENCE FIX ---
        # 1. Check if collection exists; if not, explicitly create it to ensure persistence.
        if 'exercises' not in db.list_collection_names():
            db.create_collection('exercises')
            print("Successfully created 'exercises' collection structure for persistence.")
        # --- END CRITICAL PERSISTENCE FIX ---
        
        exercises_collection = db['exercises']
        
        # We must drop the conflicting index only if it exists
        try:
            # Drop the problematic index created on the old API field names ('name', 'bodyPart')
            exercises_collection.drop_index("unique_exercise_index")
            print("Dropped conflicting Atlas index.")
        except:
            pass # Safely ignore if the index doesn't exist

        # 2. Create the NEW, CORRECT Unique Index using application field names
        try:
            exercises_collection.create_index([
                ("exercise_name", ASCENDING),
                ("body_part", ASCENDING),
                ("equipment", ASCENDING)
            ], unique=True, name="unique_app_index")
            print("Successfully created final unique_app_index.")
        except Exception as e:
            # This is expected if the index already exists from a previous successful run
            print(f"Warning: Index creation skipped/failed, likely because it already exists: {e}")
        # --- END CRITICAL FIX ---


        api_base_url = "https://exercisedb.p.rapidapi.com/exercises" 
        
        # --- API Headers and Params (Authentication is now stable) ---
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
            response.raise_for_status() 
            api_exercises = response.json()
            
            # Validation Check
            if not isinstance(api_exercises, list) or not api_exercises:
                break 

            exercises_to_insert = []

            for exercise in api_exercises:
                if not exercise.get("name") or not exercise.get("bodyPart"):
                    continue

                # --- MAPPING: STRICTLY ONLY THE 8 REQUESTED FIELDS (plus app keys) ---
                mapped_exercise = {
                    "exercise_name": exercise.get("name"),
                    "body_part": exercise.get("bodyPart"),
                    "equipment": exercise.get("equipment"),
                    "target": exercise.get("target"),
                    "secondaryMuscles": exercise.get("secondaryMuscles"),
                    "instructions": exercise.get("instructions"),
                    "description": exercise.get("description"),
                    "difficulty": exercise.get("difficulty"),
                    "id": exercise.get("id")
                }
                # --- END MAPPING ---

                # CRITICAL FIX: REMOVE find_one CHECK AND RELY ON DATABASE ERROR HANDLING
                exercises_to_insert.append(mapped_exercise)
            
            if exercises_to_insert:
                # Insert documents for the current batch
                # We use ordered=False to skip errors and keep inserting the rest
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
        # If a BulkWriteError occurs, we return the count of items successfully inserted
        print(f"BulkWriteError during insert: {e}")
        # NOTE: We rely on the error details to get the count of items inserted before the crash
        inserted_before_crash = total_inserted_count + len(e.details.get('insertedIds', []))
        return inserted_before_crash
    except Exception as e:
        print(f"An error occurred during database refresh: {e}")
        return {"error": f"Database Insertion Error: {e}"}
