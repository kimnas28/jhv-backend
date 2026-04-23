import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("MONGO_URL")


client = MongoClient(uri, server_api=ServerApi('1'))
db = client["JobSystem"]


try:

    client.admin.command('ping')
    print("Connection: Success to MongoDB Cloud!")
except Exception as e:
    print(f"Error: {e}")

users_collection = db["users"]
jobs_collection = db["jobs"]
deleted_users_collection = db["deleted_users"]