"""Safe dry-run for database_refresh: fetch one page from ExerciseDB and print mapped docs.

This script does NOT write to the database. It only validates that the external API
is reachable with the provided RAPIDAPI_KEY and that the mapping in
`database_refresh.insert_exercises_if_not_exist` produces expected fields.

Usage:
  RAPIDAPI_KEY=your_key python3 scripts/refresh_dry_run.py

If you don't want to set env vars inline, export RAPIDAPI_KEY first in your shell.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not RAPIDAPI_KEY:
    print("RAPIDAPI_KEY not found in environment. Export RAPIDAPI_KEY and retry.")
    raise SystemExit(1)

API_URL = "https://exercisedb.p.rapidapi.com/exercises"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
}

params = {"limit": "10", "offset": "0"}

print("Fetching one page from ExerciseDB (limit=10)...")
resp = requests.get(API_URL, headers=headers, params=params, timeout=30)
resp.raise_for_status()
data = resp.json()

if not isinstance(data, list):
    print("Unexpected API response format. Expected a list.")
    raise SystemExit(2)

print(f"Fetched {len(data)} exercises. Showing up to 5 mapped examples:\n")


def map_exercise(ex):
    return {
        "exercise_name": ex.get("name"),
        "body_part": ex.get("bodyPart"),
        "equipment": ex.get("equipment"),
        "target": ex.get("target"),
        "secondaryMuscles": ex.get("secondaryMuscles"),
        "instructions": ex.get("instructions"),
        "description": ex.get("description"),
        "difficulty": ex.get("difficulty"),
        "id": ex.get("id"),
    }


for ex in data[:5]:
    if not ex.get("name") or not ex.get("bodyPart"):
        continue
    mapped = map_exercise(ex)
    print(mapped)

print("\nDry-run complete. No DB writes were performed.")
