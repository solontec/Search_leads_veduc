from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))

db = client["linkedin_prospect"]
collection = db["leads"]

collection.insert_one({
    "name": "teste",
    "status": "novo"
})  

print("Banco conectado!")