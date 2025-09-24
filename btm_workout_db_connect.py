import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

db = None
client = None

def connect_db():
    global db, client
    try:
        load_dotenv()
        MONGO_USER = os.getenv("MONGO_USER")
        MONGO_PASS = os.getenv("MONGO_PASS")
        MONGO_HOST = os.getenv("MONGO_HOST")
        MONGO_DB = os.getenv("MONGO_DB")

        if not all([MONGO_USER, MONGO_PASS, MONGO_HOST, MONGO_DB]):
            print("Error: One or more required environment variables are missing.")
            return

        encoded_password = quote_plus(MONGO_PASS)
        MONGO_URI = f"mongodb://{MONGO_USER}:{encoded_password}@{MONGO_HOST}/{MONGO_DB}"
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        db = client.get_database(MONGO_DB)
        print("Successfully connected to MongoDB.")
    except ConnectionFailure as e:
        print(f"Error: Could not connect to MongoDB. Please check your connection string. {e}")
        db = None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        db = None

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
