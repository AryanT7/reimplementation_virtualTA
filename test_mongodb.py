from pymongo import MongoClient

# Use the new non-SRV connection string
uri = "mongodb://student:NEWTA123@ac-by1wfoo-shard-00-00.tgxyo7s.mongodb.net:27017,ac-by1wfoo-shard-00-01.tgxyo7s.mongodb.net:27017,ac-by1wfoo-shard-00-02.tgxyo7s.mongodb.net:27017/?ssl=true&replicaSet=atlas-b85t4w-shard-0&authSource=admin&retryWrites=true&w=majority"

try:
    client = MongoClient(uri)
    dbs = client.list_database_names()
    print("✅ Successfully connected! Databases:", dbs)
except Exception as e:
    print("❌ Connection failed:", e)
