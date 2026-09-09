import os
import json
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

# বটের পাঠানো JSON রিসিভ করার জন্য মডেল
class QueryModel(BaseModel):
    query: str = ""

@app.get("/")
def home():
    return {"Message": "API is successfully running on Render!"}

# 🌐 আপনার ওয়েবসাইটের জন্য (GET Endpoint)
@app.get("/api/data")
def get_data():
    try:
        data = list(collection.find({}).limit(100))
        parsed_data = json.loads(json_util.dumps(data))
        return {"status": "success", "total_records": len(parsed_data), "data": parsed_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 🤖 আপনার টেলিগ্রাম বটের জন্য (POST Endpoint)
@app.post("/search")
def search_api(payload: QueryModel):
    try:
        user_query = payload.query
        
        if not user_query.strip():
            # কিছু না খুঁজলে লেটেস্ট ৫টি কোর্স দেবে
            cursor = collection.find({}).sort("_id", -1).limit(5)
        else:
            # ইউজারের টেক্সট অনুযায়ী সার্চ
            smart_term = user_query.strip().replace(" ", ".*")
            search_regex = {"$regex": smart_term, "$options": "i"}
            cursor = collection.find({"title": search_regex}).limit(5)
            
        courses = list(cursor)
        
        if not courses:
            return {"text": "Sorry, I couldn't find any courses matching your query."}
            
        answer = "Here is the relevant course information from the database:\n\n"
        for c in courses:
            title = c.get('title', 'Unknown Course')
            status = c.get('status', 'N/A')
            answer += f"📌 {title}\n- Status: {status}\n\n"
            
        # বটের call_integration-এর শর্ত অনুযায়ী 'text' ভ্যারিয়েবলে ডেটা পাঠানো হচ্ছে
        return {"text": answer}
        
    except Exception as e:
        return {"text": f"Error: {str(e)}"}
