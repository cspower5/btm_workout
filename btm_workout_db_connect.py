import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import pymongo
from pymongo import MongoClient

# Initialize the db variable to None, so it always has a value.
db = None
client = None

try:
    # 1. Load environment variables
    load_dotenv()
    MONGO_USER = os.getenv("MONGO_USER")
    MONGO_PASS = os.getenv("MONGO_PASS")
    MONGO_HOST = os.getenv("MONGO_HOST")
    MONGO_DB = os.getenv("MONGO_DB")

    # 2. Check for the necessary environment variables
    if not all([MONGO_USER, MONGO_PASS, MONGO_HOST, MONGO_DB]):
        print("Error: One or more required environment variables are missing.")
    else:
        # 3. Construct the MongoDB connection URL
        encoded_password = quote_plus(MONGO_PASS)
        MONGO_URI = f"mongodb://{MONGO_USER}:{encoded_password}@{MONGO_HOST}/{MONGO_DB}"

        # 4. Connect to the MongoDB client
        client = MongoClient(MONGO_URI)
        
        # 5. Ping the database to force a connection and validate it
        client.admin.command('ping')
        
        # 6. If the connection is successful, get the database object
        db = client.get_database(MONGO_DB)
        print("Successfully connected to MongoDB.")

except pymongo.errors.ConnectionFailure as e:
    print(f"Error: Could not connect to MongoDB. Please check your connection string. {e}")
    if client:
        client.close()
except Exception as e:
    print(f"An unexpected error occurred during database connection: {e}")
    if client:
        client.close()
