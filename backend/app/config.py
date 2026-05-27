import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "rag_documents")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 300
    CHUNK_OVERLAP: int = 30
    TOP_K_RETRIEVAL: int = 2
    SIMILARITY_THRESHOLD: float = 0.3

    # ✅ FIXED: Much higher timeouts for RAGAS evaluation
    OLLAMA_TIMEOUT: float = 300.0        # 5 minutes for RAG queries
    RAGAS_OLLAMA_TIMEOUT: float = 600.0  # 10 minutes for RAGAS (it calls LLM many times)
    RAGAS_MAX_RETRIES: int = 3

settings = Settings()