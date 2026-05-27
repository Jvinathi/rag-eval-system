import logging
from fastapi import APIRouter, HTTPException
from app.services.eval_service import eval_service
from app.models.schemas import EvalRequest, EvalResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/evaluate", response_model=EvalResponse)
async def evaluate_response(request: EvalRequest):
    """
    Evaluate a RAG response using RAGAS metrics.
    Computes: faithfulness, answer_relevancy, context_precision
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    if not request.contexts:
        raise HTTPException(status_code=400, detail="At least one context is required.")
    
    try:
        result = await eval_service.evaluate_response(
            question=request.question,
            answer=request.answer,
            contexts=request.contexts,
            ground_truth=request.ground_truth,
        )
        return result
    
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/metrics/history")
async def get_metrics_history():
    """Return all past evaluation results for the dashboard."""
    return {
        "history": eval_service.get_history(),
        "summary": eval_service.get_summary_stats(),
    }


@router.get("/metrics/summary")
async def get_metrics_summary():
    """Return aggregated statistics."""
    return eval_service.get_summary_stats()