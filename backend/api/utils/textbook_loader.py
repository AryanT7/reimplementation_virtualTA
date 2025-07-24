from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from typing import List, Optional
from uuid import uuid4
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from api.database.mongodb import MongoDB
from api.utils.logger import logger
import os
import time

class TextbookLoader:
    def __init__(self,
                 chunk_size: int = 2000,
                 chunk_overlap: int = 200,
                 collection_name: str = os.getenv("VECTOR_COLLECTION", "combined_vectors"),
                 index_name: str = os.getenv("VECTOR_INDEX", "combined_index")):

        self.collection_name = collection_name
        self.index_name = index_name
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

        if MongoDB.db is None:
            MongoDB.connect_db()

        self.db = MongoDB.get_db()
        self.collection = self.db[self.collection_name]

        self.vector_store = MongoDBAtlasVectorSearch(
            collection=self.collection,
            embedding=self.embeddings,
            index_name=self.index_name,
            relevance_score_fn="cosine",
        )

        self._ensure_vector_index()

    def _ensure_vector_index(self):
        try:
            if self.collection_name not in self.db.list_collection_names():
                self.db.create_collection(self.collection_name)
                logger.info(f"Created collection '{self.collection_name}'")

            existing_indexes = [idx["name"] for idx in self.collection.list_search_indexes()]
            if self.index_name not in existing_indexes:
                self.vector_store.create_search_index(
                    definition={
                        "fields": [
                            {
                                "type": "vector",
                                "path": "embedding",
                                "numDimensions": 3072,
                                "similarity": "cosine",
                            },
                            {
                                "path": "metadata.source",
                                "type": "filter",
                            },
                        ]
                    },
                    name=self.index_name,
                )
                logger.info(f"Created vector index '{self.index_name}' in MongoDB")
            else:
                logger.info(f"Vector index '{self.index_name}' already exists")

        except Exception as e:
            msg = str(e)
            if "already exists" in msg or "IndexAlreadyExists" in msg:
                logger.info(f"Index already exists: {msg}")
            else:
                logger.error(f"Failed to create vector index '{self.index_name}': {msg}")
                raise

    def load_textbook(self, directory: str, file_name: str) -> List[Document]:
        try:
            loader = PyPDFLoader(file_path=directory)
            raw_docs = loader.load()

            splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
            final_docs = []

            for i, doc in enumerate(raw_docs):
                page_content = doc.page_content.strip()
                if not page_content:
                    continue

                doc.metadata["source"] = file_name
                doc.metadata["page_number"] = i + 1

                if len(page_content) > 12000:
                    logger.warning(f"Page {i + 1} is very large, will split into smaller chunks.")
                    chunks = splitter.split_documents([doc])
                    for chunk in chunks:
                        chunk.metadata = doc.metadata
                    final_docs.extend(chunks)
                else:
                    final_docs.append(doc)

            logger.info(f"Prepared {len(final_docs)} chunks (page-based + fallback split)")

            # Updated: Batching to avoid 300K token limit
            batch_size = 50
            ids = [str(uuid4()) for _ in final_docs]
            for i in range(0, len(final_docs), batch_size):
                batch_docs = final_docs[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]

                try:
                    self.vector_store.add_documents(documents=batch_docs, ids=batch_ids)
                    logger.info(f"Batch {i//batch_size + 1}: Stored {len(batch_docs)} chunks")
                    time.sleep(0.5)  # optional: slow down to avoid rate limit
                except Exception as e:
                    logger.error(f"Batch {i//batch_size + 1} failed: {e}")
                    raise

            return final_docs

        except Exception as e:
            logger.error(f"Error processing textbook: {e}")
            raise

if __name__ == "__main__":
    loader = TextbookLoader()
    path = "api/utils/tapdf/ECE506_textbook.pdf"
    loader.load_textbook(path, "ECE506_textbook.pdf")
