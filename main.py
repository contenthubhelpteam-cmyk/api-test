import os
import json
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import json_util

app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['assetprim_uploader'] 
collection = db['upload_logs'] 

class QueryModel(BaseModel):
    query: str = ""

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

# 🤖 বটের স্মার্ট সার্চ এন্ডপয়েন্ট (Beautiful AI Context Formatting)
@app.post("/search")
def search_api(payload: QueryModel):
    try:
        q = (payload.query or "").lower()
        
        # 1) Stopwords বাদ দিয়ে keyword বের করা
        stop = {"ase", "naki", "ki", "course", "koi", "ache", "hobe", "er", "a", "the", "do", "you", "have", "any", "is", "there", "কি", "আছে", "কোর্স", "নাকি", "চাই", "লাগবে", "chai", "lagbe"}
        
        raw_words = re.split(r'[\s,?!।]+', q)
        words = [w for w in raw_words if w and w not in stop]
        
        if not words:
            cursor = collection.find({}).sort("_id", -1).limit(5)
        else:
            # 2) Partial (contains) search
            or_clauses = [{"title": {"$regex": w, "$options": "i"}} for w in words]
            cursor = collection.find({"$or": or_clauses}).limit(5)
            
        courses = list(cursor)
        
        if not courses:
            return {"context": "No matching courses found in the database for this specific query."}
            
        # 3) AI-এর জন্য সুন্দর করে গুছিয়ে Context তৈরি করা
        context_header = "Here are the exact matching courses found in the database:\n"
        context_parts = []
        
        for idx, c in enumerate(courses, 1):
            title = c.get("title", "Unknown Course")
            status = c.get("status", "Not Specified")
            
            # আপনার ডাটাবেসে অন্য ফিল্ড থাকলে এখানে যুক্ত করতে পারেন:
            # price = c.get("price", "Free")
            # item_text = f"{idx}. 📚 Course Name: {title}\n   🔹 Price: {price}\n   🔹 Status: {status}"
            
            item_text = f"{idx}. 📚 Course Name: {title}\n   🔹 Status: {status}"
            context_parts.append(item_text)
            
        # লাইন ব্রেক দিয়ে ডেটাগুলো জোড়া লাগানো
        answer = context_header + "\n" + "\n\n".join(context_parts)
        
        return {"context": answer}
        
    except Exception as e:
        return {"context": f"System Error while fetching courses: {str(e)}"}
