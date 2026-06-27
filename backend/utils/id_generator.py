import datetime
from pymongo import MongoClient
from config import *

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
complaints = db["complaints"]

def generate_id():
    year = datetime.datetime.now().year
    count = complaints.count_documents({})
    return f"CS-{year}-{count+1:05d}"