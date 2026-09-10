import os
import json
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import json_util

app = FastAPI()

# CORS Setup (ওয়েবসাইটের জন্য)
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

# 🤖 বটের জন্য স্মার্ট সার্চ এন্ডপয়েন্ট (Stopwords + Keyword Logic)
@app.post("/search")
def search_api(payload: QueryModel):
    try:
        q = (payload.query or "").lower()
        
        # 1) stopword বাদ দিয়ে keyword বের করা
        stop = {"ase", "naki", "ki", "course", "koi", "ache", "hobe", "er", "a", "the", "do", "you", "have", "any", "is", "there", "কি", "আছে", "কোর্স", "নাকি"}
        
        # রেগুলার এক্সপ্রেশন দিয়ে স্পেস বা বিরামচিহ্ন দিয়ে ভাগ করে stopwords রিমুভ করা
        raw_words = re.split(r'[\s,?!।]+', q)
        words = [w for w in raw_words if w and w not in stop]
        
        if not words:
            # যদি শুধু stop words থাকে (যেমন: "course ki ase?"), তখন লেটেস্ট ৫টি কোর্স দিবে
            cursor = collection.find({}).sort("_id", -1).limit(5)
        else:
            # 2) প্রতিটা keyword দিয়ে partial (contains) search — যেকোনো একটা মিললেই
            or_clauses = []
            for w in words:
                or_clauses.append({"title": {"$regex": w, "$options": "i"}})
                
                # ⚠️ আপনার ডাটাবেসে যদি category বা tags নামে ফিল্ড থাকে, তবে নিচের লাইনগুলো আনকমেন্ট করে দেবেন:
                # or_clauses.append({"category": {"$regex": w, "$options": "i"}})
                # or_clauses.append({"tags": {"$regex": w, "$options": "i"}})
            
            # MongoDB তে $or দিয়ে কোয়েরি করা হচ্ছে
            cursor = collection.find({"$or": or_clauses}).limit(5)
            
        courses = list(cursor)
        
        if not courses:
            return {"context": "No matching course found."}
            
        # 3) Context সাজানো (আপনার JS কোডের হুবহু স্টাইলে)
        context_parts = []
        for c in courses:
            title = c.get("title", "Unknown Course")
            status = c.get("status", "not available")
            
            # আপনার ডাটাবেসে price বা summary ফিল্ড থাকলে সেগুলোও যুক্ত করতে পারবেন:
            # price = c.get("price", "0")
            # summary = c.get("summary", "")
            # context_parts.append(f"{title} — {price}৳ — {status}. {summary}")
            
            # আপাতত title এবং status দিয়ে স্ট্রিং তৈরি করা হলো
            context_parts.append(f"{title} — Status: {status}")
            
        # " | " দিয়ে সবগুলো কোর্সকে একসাথে যুক্ত করা
        answer = " | ".join(context_parts)
        
        return {"context": answer}
        
    except Exception as e:
        return {"context": f"Error: {str(e)}"}
