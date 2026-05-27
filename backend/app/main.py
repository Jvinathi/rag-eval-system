import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import upload, query, metrics
from app.services.rag_service import initialize_llm_and_embeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup: initialize models.
    Runs on shutdown: cleanup.
    """
    logger.info("=" * 50)
    logger.info("Starting RAG Evaluation System...")
    logger.info("=" * 50)
    
    # Initialize LLM and embedding models
    # This downloads the embedding model on first run (~90MB)
    initialize_llm_and_embeddings()
    
    logger.info("All models loaded. Server ready!")
    yield
    
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Production RAG System with Evaluation Pipeline",
    description=(
        "Domain-specific RAG app with RAGAS evaluation. "
        "Upload PDFs, ask questions, evaluate quality — all free, all local."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allows our React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])


@app.get("/")
async def root():
    return {
        "message": "RAG Evaluation System is running!",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "rag-eval-system"}