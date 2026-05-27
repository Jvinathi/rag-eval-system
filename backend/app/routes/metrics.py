import logging
import asyncio
from fastapi import APIRouter, HTTPException
from app.services.eval_service import eval_service
from app.models.schemas import EvalRequest, EvalResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/evaluate", response_model=EvalResponse)
async def evaluate_response(request: EvalRequest):
    """
    Evaluate RAG response using RAGAS metrics.
    Note: This endpoint takes 2-5 minutes — that is expected.
    The frontend shows a loading state during this time.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not request.contexts:
        raise HTTPException(status_code=400, detail="At least one context is required.")

    # ✅ Warn if contexts are too short (RAGAS needs meaningful text)
    for i, ctx in enumerate(request.contexts):
        if len(ctx.strip()) < 20:
            logger.warning(f"Context {i} is very short ({len(ctx)} chars) — may affect scores")

    try:
        # ✅ Wrap with asyncio.wait_for so we get a clean timeout error
        result = await asyncio.wait_for(
            eval_service.evaluate_response(
                question=request.question,
                answer=request.answer,
                contexts=request.contexts,
                ground_truth=request.ground_truth,
            ),
            timeout=700.0,  # 11 minutes max — slightly more than RAGAS internal timeout
        )
        return result

    except asyncio.TimeoutError:
        logger.error("RAGAS evaluation timed out after 700 seconds")
        raise HTTPException(
            status_code=504,
            detail=(
                "Evaluation timed out. "
                "Try with a shorter answer or fewer context chunks. "
                "Also make sure Ollama is running: ollama serve"
            ),
        )
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/metrics/history")
async def get_metrics_history():
    return {
        "history": eval_service.get_history(),
        "summary": eval_service.get_summary_stats(),
    }


@router.get("/metrics/summary")
async def get_metrics_summary():
    return eval_service.get_summary_stats()