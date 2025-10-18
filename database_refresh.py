import requests
import os
from dotenv import load_dotenv
from btm_workout_db_connect import get_db
from pymongo.errors import BulkWriteError
from pymongo import ASCENDING

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
    # If limit == 0, treat as 'fetch all in one request' (no pagination)
    limit = 0
    offset = 0
    # --- END PAGINATION SETUP ---

    try:
        # --- CRITICAL PERSISTENCE FIX ---
        # 1. Check if collection exists; if not, explicitly create it to ensure persistence.
        if "exercises" not in db.list_collection_names():
            db.create_collection("exercises")
            print(
                "Successfully created 'exercises' collection structure for persistence."
            )
        # --- END CRITICAL PERSISTENCE FIX ---

        exercises_collection = db["exercises"]

        # Drop old indexes if they exist
        try:
            exercises_collection.drop_index("unique_exercise_index")
            print("Dropped conflicting Atlas index: unique_exercise_index")
        except Exception:
            pass

        try:
            exercises_collection.drop_index("unique_app_index")
            print("Dropped old index: unique_app_index")
        except Exception:
            pass

        # Create the unique index matching Atlas: (name, body_part, equipment, user_id)
        try:
            exercises_collection.create_index(
                [
                    ("name", ASCENDING),
                    ("body_part", ASCENDING),
                    ("equipment", ASCENDING),
                    ("user_id", ASCENDING),
                ],
                unique=True,
                name="unique_exercises_index",
            )
            print(
                "Successfully created unique_exercises_index with (name, body_part, equipment, user_id)."
            )
        except Exception as e:
            print(
                f"Warning: Index creation skipped/failed, likely because it already exists: {e}"
            )
        # --- END CRITICAL FIX ---

        api_base_url = "https://exercisedb.p.rapidapi.com/exercises"

        # --- API Headers and Params (Authentication is now stable) ---
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
        }

        print("--- Starting Paginated API Fetch from ExerciseDB ---")

        while True:
            # If limit == 0, request all rows in a single call (no offset)
            if limit == 0:
                params = {"limit": "0"}
            else:
                params = {"limit": str(limit), "offset": str(offset)}

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

                # --- MAPPING: Use snake_case field names matching Atlas indexes ---
                # Store normalized name (lowercase) as the canonical 'name' field
                orig_name = exercise.get("name") or ""
                orig_body = exercise.get("bodyPart") or ""
                orig_equip = exercise.get("equipment") or ""

                mapped_exercise = {
                    # Use 'name' as the canonical field (normalized, lowercase)
                    "name": orig_name.strip().lower(),
                    "body_part": orig_body.strip().lower(),
                    "equipment": orig_equip.strip().lower(),
                    "target": exercise.get("target"),
                    "secondaryMuscles": exercise.get("secondaryMuscles"),
                    "instructions": exercise.get("instructions"),
                    "description": exercise.get("description"),
                    "difficulty": exercise.get("difficulty"),
                    "id": exercise.get("id"),
                    "user_id": "public",  # Public data from API has "public" user_id
                }
                # --- END MAPPING ---

                exercises_to_insert.append(mapped_exercise)

            # Insert documents for the current batch (once per page or single fetch)
            if exercises_to_insert:
                result = exercises_collection.insert_many(
                    exercises_to_insert, ordered=False
                )
                total_inserted_count += len(result.inserted_ids)

            # If limit == 0 we fetched everything in one call; break
            if limit == 0:
                break

            # Update offset for the next page
            offset += limit

            # If the current batch was smaller than the limit, we've reached the end
            if len(api_exercises) < limit:
                break

    except requests.exceptions.RequestException as e:
        if hasattr(e, "response") and e.response is not None:
            print(f"API Request Failed: Status {e.response.status_code}")
            return {
                "error": f"API Request Failed: Status {e.response.status_code}. Check key/host."
            }
        else:
            print(f"Network Error: {e}")
            return {"error": f"Network Error during API fetch: {e}"}
    except BulkWriteError as e:
        # If a BulkWriteError occurs, we return the count of items successfully inserted
        print(f"BulkWriteError during insert: {e}")
        # NOTE: We rely on the error details to get the count of items inserted before the crash
        inserted_before_crash = total_inserted_count + len(
            e.details.get("insertedIds", [])
        )
        return inserted_before_crash
    except Exception as e:
        print(f"An error occurred during database refresh: {e}")
        return {"error": f"Database Insertion Error: {e}"}

    finally:
        # Always attempt to sync management collections even if refresh had errors
        try:
            if db is not None:
                print(
                    "Post-refresh: syncing distinct body_part and equipment to management collections..."
                )

                # Drop old indexes without user_id
                try:
                    db.body_parts.drop_index("unique_body_parts_name")
                    print("Dropped old body_parts index without user_id")
                except Exception:
                    pass

                try:
                    db.equipment.drop_index("unique_equipment_name")
                    print("Dropped old equipment index without user_id")
                except Exception:
                    pass

                # Create compound indexes with user_id matching Atlas
                db.body_parts.create_index(
                    [("name", ASCENDING), ("user_id", ASCENDING)],
                    unique=True,
                    name="unique_body_part_index",
                )
                db.equipment.create_index(
                    [("name", ASCENDING), ("user_id", ASCENDING)],
                    unique=True,
                    name="unique_equipment_index",
                )

                body_parts = [bp for bp in db.exercises.distinct("body_part") if bp]
                equipment_vals = [eq for eq in db.exercises.distinct("equipment") if eq]

                for bp in body_parts:
                    db.body_parts.update_one(
                        {"name": bp, "user_id": "public"},
                        {"$setOnInsert": {"name": bp, "user_id": "public"}},
                        upsert=True,
                    )

                for eq in equipment_vals:
                    db.equipment.update_one(
                        {"name": eq, "user_id": "public"},
                        {"$setOnInsert": {"name": eq, "user_id": "public"}},
                        upsert=True,
                    )

                print(
                    f"Synced {len(body_parts)} body_parts and {len(equipment_vals)} equipment entries with user_id='public'."
                )
        except Exception as e:
            print(f"Warning: Failed to sync management collections in finally: {e}")
