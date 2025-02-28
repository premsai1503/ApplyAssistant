from pymongo import MongoClient
import os
from dotenv import load_dotenv


load_dotenv()

MONGO_URL = os.getenv("MONGO_DB_URL")

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client.get_database("form_details")
collection = db.get_collection("collection0")

def validation_check(data):
    if not data.get("FirstName"):
        return {"success": False, "error": "First name is required."}
    if not data.get("LastName"):
        return {"success": False, "error": "Last name is required."}
    if not data["PermanentAccountNumber"].isdigit():
        return {"success": False, "error": "Permanent account number must be numeric."}
    return {"success": True}

def form_data_submit(data):
    try:
        validation = validation_check(data)
        if not validation["success"]:
            return validation
        result = collection.insert_one(data)
        return {"Success": True, "message": "The data entered has successfully been submitted to the database."}
    except Exception as e:
        return {"success": False, "error": str(e)}
