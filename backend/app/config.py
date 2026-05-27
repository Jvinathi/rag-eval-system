import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Ollama (free local LLM)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    
    # Embedding model (free, runs locally)
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    
    # ChromaDB vector store
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "rag_documents")
    
    # File uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    MAX_FILE_SIZE_MB: int = 50
    
    # RAG settings
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 3
    SIMILARITY_THRESHOLD: float = 0.3

settings = Settings()