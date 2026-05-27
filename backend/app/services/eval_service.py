import logging
from typing import List, Optional
from datetime import datetime
import asyncio

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
)
from langchain_community.llms import Ollama as LangchainOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import settings
from app.models.schemas import EvalMetrics, EvalResponse

logger = logging.getLogger(__name__)

# Store evaluation history in memory (for dashboard)
eval_history: List[dict] = []


def get_ragas_llm_and_embeddings():
    """
    RAGAS needs LangChain-compatible LLM and embeddings.
    We use the same free Ollama + HuggingFace models.
    """
    llm = LangchainOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
    )
    
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.EMBED_MODEL,
        model_kwargs={"device": "cpu"},
    )
    
    return llm, embeddings


class EvalService:
    """
    Evaluates RAG system quality using RAGAS metrics:
    
    1. FAITHFULNESS: Is the answer grounded in the retrieved context?
       (0 = hallucinated, 1 = fully supported by context)
    
    2. ANSWER RELEVANCY: Does the answer actually address the question?
       (0 = irrelevant, 1 = perfectly relevant)
    
    3. CONTEXT PRECISION: Are the retrieved chunks actually useful?
       (0 = retrieved junk, 1 = retrieved perfect chunks)
    """
    
    def __init__(self):
        self._llm = None
        self._embeddings = None
    
    def _get_models(self):
        """Lazy-load models to avoid startup delay."""
        if self._llm is None:
            self._llm, self._embeddings = get_ragas_llm_and_embeddings()
        return self._llm, self._embeddings
    
    async def evaluate_response(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> EvalResponse:
        """
        Run RAGAS evaluation on a single Q&A pair.
        
        Args:
            question: The user's question
            answer: The RAG system's answer
            contexts: List of retrieved document chunks
            ground_truth: Optional correct answer (for reference)
        
        Returns:
            EvalResponse with all metric scores
        """
        logger.info(f"Evaluating response for: {question[:80]}...")
        
        llm, embeddings = self._get_models()
        
        # RAGAS expects data in this specific format
        eval_data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],  # List of lists
            "ground_truth": [ground_truth or ""],
        }
        
        dataset = Dataset.from_dict(eval_data)
        
        # Run evaluation (this calls Ollama locally)
        try:
            # Run in thread to avoid blocking async event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: evaluate(
                    dataset,
                    metrics=[
                        faithfulness,
                        answer_relevancy,
                        context_precision,
                    ],
                    llm=llm,
                    embeddings=embeddings,
                    raise_exceptions=False,
                )
            )
            
            # Extract scores (default to 0 if evaluation fails)
            faith_score = float(result["faithfulness"] or 0.0)
            relevancy_score = float(result["answer_relevancy"] or 0.0)
            precision_score = float(result["context_precision"] or 0.0)
            
        except Exception as e:
            logger.error(f"RAGAS evaluation error: {e}")
            # Provide default scores with error note
            faith_score = 0.0
            relevancy_score = 0.0
            precision_score = 0.0
        
        # Calculate overall score (simple average)
        overall = (faith_score + relevancy_score + precision_score) / 3
        
        metrics = EvalMetrics(
            faithfulness=round(faith_score, 4),
            answer_relevancy=round(relevancy_score, 4),
            context_precision=round(precision_score, 4),
            overall_score=round(overall, 4),
        )
        
        timestamp = datetime.now().isoformat()
        
        # Store in history for dashboard
        eval_history.append({
            "timestamp": timestamp,
            "question": question[:100],
            "faithfulness": metrics.faithfulness,
            "answer_relevancy": metrics.answer_relevancy,
            "context_precision": metrics.context_precision,
            "overall_score": metrics.overall_score,
        })
        
        # Keep only last 50 evaluations in memory
        if len(eval_history) > 50:
            eval_history.pop(0)
        
        logger.info(f"Eval complete — Faithfulness: {faith_score:.3f}, "
                   f"Relevancy: {relevancy_score:.3f}, "
                   f"Precision: {precision_score:.3f}")
        
        return EvalResponse(
            metrics=metrics,
            timestamp=timestamp,
            question=question,
        )
    
    def get_history(self) -> List[dict]:
        """Return evaluation history for dashboard."""
        return eval_history
    
    def get_summary_stats(self) -> dict:
        """Calculate average metrics across all evaluations."""
        if not eval_history:
            return {
                "total_evaluations": 0,
                "avg_faithfulness": 0.0,
                "avg_answer_relevancy": 0.0,
                "avg_context_precision": 0.0,
                "avg_overall": 0.0,
            }
        
        n = len(eval_history)
        return {
            "total_evaluations": n,
            "avg_faithfulness": round(
                sum(e["faithfulness"] for e in eval_history) / n, 4
            ),
            "avg_answer_relevancy": round(
                sum(e["answer_relevancy"] for e in eval_history) / n, 4
            ),
            "avg_context_precision": round(
                sum(e["context_precision"] for e in eval_history) / n, 4
            ),
            "avg_overall": round(
                sum(e["overall_score"] for e in eval_history) / n, 4
            ),
        }


# Single instance
eval_service = EvalService()