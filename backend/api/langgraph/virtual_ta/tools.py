import os
import traceback
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from api.database.mongodb import MongoDB
from dotenv import load_dotenv








# Use a single combined collection & index for textbooks\VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION", "combined_vectors")\VECTOR_INDEX      = os.getenv("VECTOR_INDEX",      "combined_index")
load_dotenv()








# now point at one combined collection & index
VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION",  "combined_vectors")
VECTOR_INDEX      = os.getenv("VECTOR_INDEX",       "combined_index")
















@tool
def get_textbook_context(query: str):
  """
  Retrieve relevant textbook passages for the given query via vector search.
  """
  try:
      print(f"get_textbook_context received query: '{query}'")
      if not query or not isinstance(query, str):
          return {"error": f"Invalid query parameter: {query!r}"}








      # Ensure DB connection
      if MongoDB.db is None:
          MongoDB.connect_db()
      db = MongoDB.get_db()
      collection = db[VECTOR_COLLECTION]








      # Build vector store
      vector_store = MongoDBAtlasVectorSearch(
          embedding=OpenAIEmbeddings(model="text-embedding-3-large"),
          collection=collection,
          index_name=VECTOR_INDEX,
          relevance_score_fn="cosine",
      )








      print(f"Executing vector search on '{VECTOR_COLLECTION}' with query: '{query}'")
      results = vector_store.similarity_search_with_score(query, k=5)








      contexts = []
      for doc, score in results:
       page = doc.metadata.get("page_number", "unknown")
       print(f"* [SIM={score:.3f}] Page {page}: {doc.page_content[:200]}...")
       contexts.append({
           "page_number": page,
           "content": doc.page_content,
           "metadata": doc.metadata,
           "similarity_score": score,
        })












      print(f"Retrieved {len(contexts)} contexts")
      return {"contexts": contexts}








  except Exception as e:
      error_details = traceback.format_exc()
      print(f"Error in get_textbook_context: {str(e)}\n{error_details}")
      return {"error": str(e)}








# Export only the one tool
tools = [get_textbook_context]


