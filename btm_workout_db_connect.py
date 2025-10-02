import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

db = None
client = None


def connect_db():
    """Connect to MongoDB using environment variables if provided.

    Priority:
    1. MONGO_URI (Atlas or single URI)
    2. MONGO_USER/MONGO_PASS/MONGO_HOST (local with auth)
    3. Fallback to localhost without auth (useful for tests/monkeypatching)
    """
    global db, client
    load_dotenv()

    MONGO_DB = os.getenv("MONGO_DB", "btm_workout_db")
    MONGO_URI_ATLAS = os.getenv("MONGO_URI")

    if MONGO_URI_ATLAS:
        FINAL_MONGO_URI = MONGO_URI_ATLAS
        print("Connecting with MONGO_URI (Atlas/Deployment).")
    else:
        MONGO_USER = os.getenv("MONGO_USER")
        MONGO_PASS = os.getenv("MONGO_PASS")
        MONGO_HOST = os.getenv("MONGO_HOST")

        if not all([MONGO_USER, MONGO_PASS, MONGO_HOST]):
            # Fall back to localhost:27017 (no auth) for local development/tests
            print(
                "⚠️ Warning: Missing MONGO_USER/MONGO_PASS/MONGO_HOST; "
                "falling back to localhost without auth for local/test usage."
            )
            FINAL_MONGO_URI = f"mongodb://localhost:27017/{MONGO_DB}"
        else:
            encoded_password = quote_plus(MONGO_PASS)
            FINAL_MONGO_URI = f"mongodb://{MONGO_USER}:{encoded_password}@{MONGO_HOST}:27017/{MONGO_DB}"
            print(f"Connecting with Local URI: {MONGO_HOST}")

    try:
        client = MongoClient(FINAL_MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client.get_database(MONGO_DB)
        print(f"✅ Successfully connected to MongoDB database: {MONGO_DB}")
    except ConnectionFailure as e:
        print(
            f"❌ Error: Could not connect to MongoDB. Check Atlas Firewall status or local server. Error: {e}"
        )
        db = None
        client = None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        db = None
        client = None


def get_db():
    global db, client
    if client is not None:
        try:
            client.admin.command("ping")
            return db
        except ConnectionFailure:
            print("Connection dropped. Reconnecting...")
            db = None
            client = None

    if db is None:
        connect_db()

    return db
