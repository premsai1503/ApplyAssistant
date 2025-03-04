from pymongo import MongoClient
import os
from dotenv import load_dotenv


load_dotenv()

MONGO_URL = os.getenv("MONGO_DB_URL")

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client.get_database("Apply_Assistant")
collection = db.get_collection("form_submissions")

def validation_check(data):
    required_fields = [
        "SSN", "MobileNumber", "FirstName", "LastName", 
        "PassportNumber", "DateofBirth"
    ]
    
    for field in required_fields:
        if not data.get(field):
            return {"success": False, "error": f"{field} is required."}
    # if not data.get("FirstName"):
    #     return {"success": False, "error": "First name is required."}
    # if not data.get("LastName"):
    #     return {"success": False, "error": "Last name is required."}
    # if not data["PermanentAccountNumber"].isdigit():
    #     return {"success": False, "error": "Permanent account number must be numeric."}
    return {"success": True}

def form_data_submit(data):
    try:
        validation = validation_check(data)
        if not validation["success"]:
            return {
                "success": False,
                "errors": validation["errors"]
            }
        result = collection.insert_one(data)
        return {
            "Success": True,
            "inserted_id": str(result.inserted_id),
            "message": "The data entered has successfully been submitted to the database."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}"
        }
