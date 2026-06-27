from pymongo import MongoClient
from config import *
import bcrypt

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db["users"]

def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    users.insert_one({
        "username": username,
        "password": hashed,
        "role": "user"
    })

def verify_user(username, password):
    user = users.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode(), user["password"]):
        return user
    return None