#!/usr/bin/env python
# coding: utf-8

# In[104]:


import os
import sys
import requests
import json
from btm_workout_db_connect import db

# --- Configuration ---
# You can adjust these values based on API limits and performance needs.
ITEMS_PER_PAGE = 200  # Number of exercises to fetch per request.


# In[105]:


# 1. Load environment variables from the .env file
# This assumes the .env file is in the same directory as this script.
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    print("Error: The RAPIDAPI_KEY environment variable is missing.")
    print("Please ensure it is set in your .env file.")
    sys.exit()


# In[106]:


# 3. Check if the database connection was successful.
if db is None:
    print("Error: The database connection failed. Cannot proceed with API data insertion.")
    sys.exit()

# Get the collection object directly from the imported 'db' object.
exercises_collection = db['exercises']
print(f"Connected to database '{db.name}' and collection '{exercises_collection.name}'.")


# In[107]:


# 4. Retrieve all exercises from the API using pagination
print("\nStarting to retrieve all exercises from the API...")
all_exercises = []
offset = 0
headers = {
    'X-RapidAPI-Key': RAPIDAPI_KEY,
    'X-RapidAPI-Host': "exercisedb.p.rapidapi.com"
}

while True:
    url = f"https://exercisedb.p.rapidapi.com/exercises?limit={ITEMS_PER_PAGE}&offset={offset}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        page_data = response.json()

        if not page_data:
            print("End of exercises reached. All pages retrieved.")
            break

        all_exercises.extend(page_data)
        print(f"Retrieved {len(page_data)} exercises (offset: {offset}). Total so far: {len(all_exercises)}")

        offset += ITEMS_PER_PAGE

        # Optional: Add a small delay to avoid hitting API rate limits.
        # time.sleep(1)

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the API: {e}")
        break
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from API response.")
        break
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        break


# In[108]:


# 5. Insert data into MongoDB
if all_exercises:
    try:
        # Clear existing data to avoid duplicates
        exercises_collection.delete_many({})

        # Insert all new exercises
        insert_result = exercises_collection.insert_many(all_exercises)
        print(f"\nSuccessfully inserted {len(insert_result.inserted_ids)} new documents into MongoDB.")
    except Exception as e:
        print(f"\nFailed to insert data into MongoDB: {e}")
else:
    print("\nNo exercises were retrieved from the API. Skipping insertion.")

# 7. Count documents in the local MongoDB database and print the total
total_documents = exercises_collection.count_documents({})
print(f"Total number of exercises in the database: {total_documents}")


# In[109]:


# 7. Close the connection
if client:
    client.close()
    print("MongoDB connection closed.")

