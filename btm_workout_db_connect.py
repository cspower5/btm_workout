import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

db = None
client = None

def connect_db():
    global db, client
    # Load .env file variables immediately
    load_dotenv()
    
    # 1. Define the database name (default used if not set)
    MONGO_DB = os.getenv("MONGO_DB", "btm_workout_db")
    
    # 2. Check for single MONGO_URI (Used for Atlas/Deployment)
    MONGO_URI_ATLAS = os.getenv("MONGO_URI")

    if MONGO_URI_ATLAS:
        # Priority 1: Use the Atlas URI directly
        FINAL_MONGO_URI = MONGO_URI_ATLAS
        print("Connecting with MONGO_URI (Atlas/Deployment).")
    else:
        # Priority 2: Fallback: Build URI from components (Used for Local Development)
        MONGO_USER = os.getenv("MONGO_USER")
        MONGO_PASS = os.getenv("MONGO_PASS")
        MONGO_HOST = os.getenv("MONGO_HOST")

        if not all([MONGO_USER, MONGO_PASS, MONGO_HOST]):
            print("❌ Error: Cannot connect. Missing required local environment variables (MONGO_USER, etc.).")
            return

        encoded_password = quote_plus(MONGO_PASS)
        # Assumes default MongoDB port 27017 for local connections
        FINAL_MONGO_URI = f"mongodb://{MONGO_USER}:{encoded_password}@{MONGO_HOST}:27017/{MONGO_DB}"
        print(f"Connecting with Local URI: {MONGO_HOST}")

    try:
        # Attempt connection using the determined URI
        client = MongoClient(FINAL_MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db = client.get_database(MONGO_DB) 
        print(f"✅ Successfully connected to MongoDB database: {MONGO_DB}")
        
    except ConnectionFailure as e:
        # Handles Atlas firewall block or local server being down
        print(f"❌ Error: Could not connect to MongoDB. Check Atlas Firewall status or local server. Error: {e}")
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
            # Check if the connection is still alive with a ping
            client.admin.command('ping')
            return db
        except ConnectionFailure:
            print("Connection dropped. Reconnecting...")
            db = None
            client = None
    
    # Reconnect if db is None or if the ping failed
    if db is None:
        connect_db()
    
    return db
