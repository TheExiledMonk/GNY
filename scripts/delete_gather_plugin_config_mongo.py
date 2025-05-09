"""
Directly delete the gather_plugin config for a given pipeline from MongoDB.
Usage: python3 scripts/delete_gather_plugin_config_mongo.py [pipeline]
If pipeline is not provided, defaults to 'default'.
Requires pymongo (pip install pymongo)
"""
import sys
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "gny"  # Change if your DB name is different
COLLECTION = "plugin_configs"

pipeline = sys.argv[1] if len(sys.argv) > 1 else 'default'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
result = db[COLLECTION].delete_many({"plugin_id": "gather_plugin", "pipeline": pipeline})
print(f"Deleted {result.deleted_count} gather_plugin config(s) for pipeline '{pipeline}' from MongoDB.")
