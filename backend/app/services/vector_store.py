import chromadb
from chromadb.config import Settings as ChromaSettings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    Manages ChromaDB vector store operations.
    ChromaDB stores document embeddings so we can do similarity search.
    """
    
    def __init__(self):
        # Initialize ChromaDB client (runs in-process, no server needed)
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB initialized at: {settings.CHROMA_DB_PATH}")
    
    def get_or_create_collection(self, collection_name: str):
        """Get existing collection or create new one."""
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        logger.info(f"Collection '{collection_name}' ready with {collection.count()} documents")
        return collection
    
    def get_vector_store(self, collection_name: str) -> ChromaVectorStore:
        """Returns LlamaIndex-compatible vector store."""
        collection = self.get_or_create_collection(collection_name)
        return ChromaVectorStore(chroma_collection=collection)
    
    def get_storage_context(self, collection_name: str) -> StorageContext:
        """Returns storage context for LlamaIndex indexing."""
        vector_store = self.get_vector_store(collection_name)
        return StorageContext.from_defaults(vector_store=vector_store)
    
    def list_collections(self):
        """List all available collections."""
        return [col.name for col in self.client.list_collections()]
    
    def delete_collection(self, collection_name: str):
        """Delete a collection and all its documents."""
        self.client.delete_collection(collection_name)
        logger.info(f"Deleted collection: {collection_name}")
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get number of documents in collection."""
        try:
            collection = self.client.get_collection(collection_name)
            return collection.count()
        except Exception:
            return 0

# Single instance used across the app
vector_store_manager = VectorStoreManager()