from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["linkedin_prospect"]
collection = db["leads"]

doc = {
    "name": "Teste Lead Novo",
    "headline": "debug manual",
    "linkedin_url": "https://linkedin.com/in/teste-lead-novo-123",
    "status": "novo",
    "created_at": datetime.utcnow()
}

result = collection.insert_one(doc)
print("inserted_id =", result.inserted_id)