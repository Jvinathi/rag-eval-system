from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class QueryRequest(BaseModel):
    question: str
    collection_name: Optional[str] = "rag_documents"

class SourceNode(BaseModel):
    text: str
    score: float
    file_name: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceNode]
    retrieval_score: float
    query_id: str

class EvalMetrics(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    overall_score: float

class EvalRequest(BaseModel):
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None

class EvalResponse(BaseModel):
    metrics: EvalMetrics
    timestamp: str
    question: str

class UploadResponse(BaseModel):
    message: str
    file_name: str
    chunks_created: int
    collection_name: str