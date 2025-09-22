import requests
import os
import sys
from dotenv import load_dotenv
from btm_workout_db_connect import db

# 1. Load environment variables from the .env file
# This assumes the .env file is in the same directory as this script.
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not RAPIDAPI_KEY:
    print("Error: The RAPIDAPI_KEY environment variable is missing.")
    print("Please ensure it is set in your .env file.")
    sys.exit()


def insert_exercises_if_not_exist():
    """
    Fetches all exercises from the API and inserts them into the database
    only if they do not already exist.
    """
    if db is None:
        print("Database connection is not available.")
        return 0

    try:
        exercises_collection = db['exercises']
        
        # Now we use the environment variable directly!
        api_url = "https://exercisedb.p.rapidapi.com/exercises"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
        }

        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses
        api_exercises = response.json()

        inserted_count = 0

        for exercise in api_exercises:
            # Check if an exercise with the same name already exists
            existing_exercise = exercises_collection.find_one({"name": exercise.get("name")})

            if not existing_exercise:
                # Insert the new exercise
                exercises_collection.insert_one(exercise)
                inserted_count += 1

        return inserted_count

    except requests.exceptions.RequestException as e:
        print(f"Error fetching exercises from API: {e}")
        return 0
    except Exception as e:
        print(f"An error occurred during database refresh: {e}")
        return 0

# Note: The if __name__ == '__main__': block is removed to prevent
# this file from running automatically when imported by flask_server.py
