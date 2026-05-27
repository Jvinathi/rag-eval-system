import os
import uuid
import logging
from pathlib import Path
from typing import List, Tuple, Optional

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings as LlamaSettings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

from app.config import settings
from app.services.vector_store import vector_store_manager
from app.models.schemas import SourceNode, QueryResponse

logger = logging.getLogger(__name__)


def initialize_llm_and_embeddings():
    """
    Set up the free local LLM (Ollama/Mistral) and embedding model.
    This runs ONCE when the app starts.
    """
    logger.info("Initializing LLM and embedding model...")
    
    # Free local LLM via Ollama
    llm = Ollama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        request_timeout=600.0,
        temperature=0.1,  # Low = more factual, less creative
    )
    
    # Free embedding model (downloads once, runs locally)
    embed_model = HuggingFaceEmbedding(
        model_name=settings.EMBED_MODEL,
        trust_remote_code=True,
    )
    
    # Configure LlamaIndex to use our free models globally
    LlamaSettings.llm = llm
    LlamaSettings.embed_model = embed_model
    LlamaSettings.chunk_size = settings.CHUNK_SIZE
    LlamaSettings.chunk_overlap = settings.CHUNK_OVERLAP
    
    logger.info(f"LLM: Ollama/{settings.OLLAMA_MODEL}")
    logger.info(f"Embeddings: {settings.EMBED_MODEL}")
    return llm, embed_model


class RAGService:
    """
    Core RAG (Retrieval-Augmented Generation) service.
    
    Flow:
    1. User uploads PDF → we chunk it and embed each chunk
    2. Embeddings stored in ChromaDB
    3. User asks question → we embed the question
    4. Find similar chunks from ChromaDB
    5. Send chunks + question to local LLM
    6. LLM generates answer based ONLY on retrieved chunks
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_pdf(self, file_path: str, collection_name: str) -> int:
        """
        Process uploaded PDF:
        1. Extract text from PDF
        2. Split into chunks
        3. Generate embeddings
        4. Store in ChromaDB
        
        Returns: number of chunks created
        """
        logger.info(f"Processing PDF: {file_path}")
        
        # Step 1: Load PDF using LlamaIndex's reader
        documents = SimpleDirectoryReader(
            input_files=[file_path],
            filename_as_id=True,  # Use filename as document ID
        ).load_data()
        
        logger.info(f"Loaded {len(documents)} pages from PDF")
        
        # Step 2: Get storage context (ChromaDB collection)
        storage_context = vector_store_manager.get_storage_context(collection_name)
        
        # Step 3: Create text splitter
        splitter = SentenceSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        
        # Step 4: Build index (chunks → embeddings → ChromaDB)
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            transformations=[splitter],
            show_progress=True,
        )
        
        # Count chunks created
        chunk_count = vector_store_manager.get_collection_count(collection_name)
        logger.info(f"Created {chunk_count} chunks in collection '{collection_name}'")
        
        return chunk_count
    
    async def query(
        self, 
        question: str, 
        collection_name: str
    ) -> QueryResponse:
        """
        Answer a question using RAG:
        1. Embed the question
        2. Retrieve top-K similar chunks from ChromaDB
        3. If similarity too low → fallback response
        4. Send to Mistral LLM for answer
        5. Return answer + sources
        """
        logger.info(f"Processing query: {question[:100]}...")
        
        query_id = str(uuid.uuid4())[:8]
        
        # Get vector store for this collection
        vector_store = vector_store_manager.get_vector_store(collection_name)
        
        # Rebuild index from existing ChromaDB data
        index = VectorStoreIndex.from_vector_store(vector_store)
        
        # Configure retriever
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=settings.TOP_K_RETRIEVAL,
        )
        
        # Similarity threshold filter (auto-retrieval fallback)
        # If no chunks are similar enough, we know to fall back
        similarity_filter = SimilarityPostprocessor(
            similarity_cutoff=settings.SIMILARITY_THRESHOLD
        )
        
        # Response synthesizer — how to combine retrieved chunks + LLM
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",  # Combines chunks efficiently
        )
        
        # Build query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=[similarity_filter],
        )
        
        # Execute query
        response = query_engine.query(question)
        
        # Extract source nodes (retrieved chunks)
        sources = []
        retrieval_score = 0.0
        
        if response.source_nodes:
            scores = [node.score for node in response.source_nodes if node.score]
            retrieval_score = sum(scores) / len(scores) if scores else 0.0
            
            for node in response.source_nodes:
                sources.append(SourceNode(
                    text=node.text[:500],  # Truncate for response
                    score=node.score or 0.0,
                    file_name=node.metadata.get("file_name", "unknown"),
                ))
        
        # Auto-retrieval fallback
        answer_text = str(response)
        if not response.source_nodes or retrieval_score < settings.SIMILARITY_THRESHOLD:
            answer_text = (
                "I could not find relevant information in the uploaded documents "
                "to answer this question confidently. Please try:\n"
                "1. Rephrasing your question\n"
                "2. Uploading more relevant documents\n"
                f"Original query: {question}"
            )
            logger.warning(f"Low retrieval score ({retrieval_score:.3f}) — fallback triggered")
        
        return QueryResponse(
            answer=answer_text,
            sources=sources,
            retrieval_score=retrieval_score,
            query_id=query_id,
        )


# Single instance
rag_service = RAGService()