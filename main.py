import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import json_util

# 1. FastAPI App Setup
app = FastAPI()

# CORS Setup: আপনার ওয়েবসাইট যেন এই API থেকে ডেটা নিতে পারে
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. MongoDB Connection (Render ENV থেকে ডেটা নেবে)
MONGO_URI = os.getenv("MONGO_URI")

# যদি ENV তে লিংক না থাকে, তবে একটি এরর দেখাবে যাতে আপনি বুঝতে পারেন
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI environment variable is missing!")

client = MongoClient(MONGO_URI)
db = client['assetprim_uploader'] 
collection = db['upload_logs'] 

# 3. Endpoints
@app.get("/")
def home():
    return {"Message": "API is successfully running on Render!"}

@app.get("/api/data")
def get_data():
    try:
        data = list(collection.find({}).limit(100))
        parsed_data = json.loads(json_util.dumps(data))
        return {"status": "success", "total_records": len(parsed_data), "data": parsed_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
