import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("MONGO_URL")

if not uri:
    raise ValueError(
        "MONGO_URL environment variable is not set. "
        "Please set it to your MongoDB Atlas connection string or local MongoDB URI."
    )

client = MongoClient(uri, server_api=ServerApi('1'), retryWrites=True, w="majority")
db = client["JobSystem"]


try:
    client.admin.command('ping')
    print("Connection: Success to MongoDB!")
except Exception as e:
    print(f"Error: Connection failed - {e}")
    raise

users_collection = db["users"]
jobs_collection = db["jobs"]
deleted_users_collection = db["deleted_users"]