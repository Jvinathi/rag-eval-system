import logging
import asyncio
from typing import List, Optional
from datetime import datetime

from app.config import settings
from app.models.schemas import EvalMetrics, EvalResponse

logger = logging.getLogger(__name__)

# Store evaluation history in memory
eval_history: List[dict] = []


def run_ragas_evaluation(question: str, answer: str, contexts: List[str], ground_truth: str) -> dict:
    """
    This function runs RAGAS evaluation SYNCHRONOUSLY.
    We run it in a separate thread via asyncio.run_in_executor
    so it doesn't block FastAPI's async event loop.

    WHY SEPARATE FUNCTION:
    RAGAS internally uses its own event loop calls.
    Mixing it with FastAPI's async loop causes freezes.
    Running in executor = separate thread = no conflict.
    """
    try:
        # ── Import here (not at top) to avoid circular import issues ──
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
        )
        from langchain_community.llms import Ollama as LangchainOllama
        from langchain_community.embeddings import HuggingFaceEmbeddings

        logger.info("Initializing RAGAS models...")

        # ── LLM for RAGAS: use LangChain Ollama with high timeout ──
        llm = LangchainOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1,
            timeout=settings.RAGAS_OLLAMA_TIMEOUT,   # ✅ 10 minutes
            num_predict=512,                          # limit output tokens → faster
        )

        # ── Embedding model: same HuggingFace model ──
        embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        logger.info("Running RAGAS evaluation (this takes 2-5 minutes)...")

        # ── Build dataset in RAGAS format ──
        eval_data = {
            "question":     [question],
            "answer":       [answer],
            "contexts":     [contexts],       # list of lists
            "ground_truth": [ground_truth or answer],  # fallback to answer if no ground truth
        }
        dataset = Dataset.from_dict(eval_data)

        # ── Run evaluation ──
        result = evaluate(
            dataset=dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
            ],
            llm=llm,
            embeddings=embeddings,
            raise_exceptions=False,   # ✅ don't crash on partial failures
        )

        # ── Safely extract scores (handle NaN/None) ──
        def safe_score(key: str) -> float:
            try:
                val = result[key]
                if val is None:
                    return 0.0
                score = float(val)
                # NaN check
                return score if score == score else 0.0
            except Exception:
                return 0.0

        return {
            "faithfulness":      safe_score("faithfulness"),
            "answer_relevancy":  safe_score("answer_relevancy"),
            "context_precision": safe_score("context_precision"),
            "error": None,
        }

    except Exception as e:
        logger.error(f"RAGAS evaluation failed: {e}", exc_info=True)
        return {
            "faithfulness":      0.0,
            "answer_relevancy":  0.0,
            "context_precision": 0.0,
            "error": str(e),
        }


class EvalService:

    async def evaluate_response(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> EvalResponse:
        """
        Runs RAGAS evaluation in a thread pool executor.

        WHY EXECUTOR:
        - RAGAS is synchronous (blocking) code
        - FastAPI is async
        - Running blocking code directly in async freezes the entire server
        - run_in_executor moves it to a separate thread → server stays responsive
        """
        logger.info(f"Starting RAGAS evaluation for: '{question[:80]}...'")

        loop = asyncio.get_event_loop()

        # ✅ Run blocking RAGAS code in thread pool — won't freeze FastAPI
        scores = await loop.run_in_executor(
            None,   # uses default ThreadPoolExecutor
            run_ragas_evaluation,
            question,
            answer,
            contexts,
            ground_truth or "",
        )

        if scores.get("error"):
            logger.warning(f"Evaluation had errors: {scores['error']}")

        overall = (
            scores["faithfulness"] +
            scores["answer_relevancy"] +
            scores["context_precision"]
        ) / 3

        metrics = EvalMetrics(
            faithfulness=round(scores["faithfulness"], 4),
            answer_relevancy=round(scores["answer_relevancy"], 4),
            context_precision=round(scores["context_precision"], 4),
            overall_score=round(overall, 4),
        )

        timestamp = datetime.now().isoformat()

        # Store in history
        eval_history.append({
            "timestamp":        timestamp,
            "question":         question[:100],
            "faithfulness":     metrics.faithfulness,
            "answer_relevancy": metrics.answer_relevancy,
            "context_precision": metrics.context_precision,
            "overall_score":    metrics.overall_score,
        })

        if len(eval_history) > 50:
            eval_history.pop(0)

        logger.info(
            f"Evaluation done — F:{metrics.faithfulness:.3f} "
            f"R:{metrics.answer_relevancy:.3f} "
            f"P:{metrics.context_precision:.3f}"
        )

        return EvalResponse(
            metrics=metrics,
            timestamp=timestamp,
            question=question,
        )

    def get_history(self) -> List[dict]:
        return eval_history

    def get_summary_stats(self) -> dict:
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
            "avg_faithfulness": round(sum(e["faithfulness"] for e in eval_history) / n, 4),
            "avg_answer_relevancy": round(sum(e["answer_relevancy"] for e in eval_history) / n, 4),
            "avg_context_precision": round(sum(e["context_precision"] for e in eval_history) / n, 4),
            "avg_overall": round(sum(e["overall_score"] for e in eval_history) / n, 4),
        }


eval_service = EvalService()