import os
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
from dotenv import load_dotenv
from ..utils.logger import logger


# Load environment variables
load_dotenv()


class MongoDB:
   """
   Singleton-style MongoDB connection manager.
   Ensures the combined_vectors collection and its search index exist.
   """
   client: MongoClient = None
   db = None


   @classmethod
   def connect_db(cls):
       """
       Connect to MongoDB using URI and database name from environment.
       Ensure the combined vector collection and index are created.
       """
       mongodb_url   = os.getenv("MONGODB_URL").strip()
       database_name = os.getenv("DATABASE_NAME").strip()


       cls.client = MongoClient(mongodb_url, tls=True, tlsAllowInvalidCertificates=True)
       cls.db     = cls.client[database_name]


       # Only one combined collection/index
       coll_name = os.getenv("VECTOR_COLLECTION", "combined_vectors")
       idx_name  = os.getenv("VECTOR_INDEX",      "combined_index")
       cls._ensure_vector_index(coll_name, idx_name)


       logger.info("MongoDB connected; combined vector index ensured.")


   @classmethod
   def _ensure_vector_index(cls, collection_name: str, index_name: str):
       """
       Create the collection if missing, and then create a vector-search index on
       embedding + metadata.source if it doesn't exist.
       """
       try:
           if collection_name not in cls.db.list_collection_names():
               cls.db.create_collection(collection_name)
               logger.info(f"Created collection '{collection_name}'")


           coll = cls.db[collection_name]
           existing = [idx.get("name") for idx in coll.list_search_indexes()]


           if index_name not in existing:
               model = SearchIndexModel(
                   definition={
                       "fields": [
                           {"type": "vector",      "numDimensions": 3072, "path": "embedding",          "similarity": "cosine"},
                           {"path":"metadata.source", "type":"filter"}
                       ]
                   },
                   name=index_name,
                   type="vectorSearch"
               )
               coll.create_search_index(model=model)
               logger.info(f"Created search index '{index_name}' on '{collection_name}'")
           else:
               logger.info(f"Search index '{index_name}' already exists on '{collection_name}'")


       except Exception as e:
           # suppress benign "already exists" errors
           msg = str(e).lower()
           if "already exists" in msg:
               logger.info(f"Index '{index_name}' already exists (suppressed): {e}")
           else:
               logger.error(f"Failed to ensure index '{index_name}' on '{collection_name}': {e}")
               raise


   @classmethod
   def get_db(cls):
       """Return the active database connection."""
       return cls.db


   @classmethod
   def close_db(cls):
       """Close the MongoDB client connection."""
       if cls.client:
           cls.client.close()
           logger.info("Closed MongoDB connection")


