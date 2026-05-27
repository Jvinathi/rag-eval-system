import logging
from fastapi import APIRouter, HTTPException
from app.services.rag_service import rag_service
from app.models.schemas import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Answer a question using RAG over indexed documents.
    
    Auto-retrieval fallback: if no relevant docs found,
    returns a helpful fallback message.
    """
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )
    
    if len(request.question) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Question too long (max 1000 characters)."
        )
    
    try:
        response = await rag_service.query(
            question=request.question,
            collection_name=request.collection_name,
        )
        return response
    
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )