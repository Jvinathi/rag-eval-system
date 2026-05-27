# Production RAG System with Evaluation Pipeline

> "Chatbots hallucinate — mine doesn't, and here's the proof."

A domain-specific RAG application with a full RAGAS evaluation harness. 
Built entirely with free, local models — no API keys required.

## Tech Stack
- **LLM**: Ollama + Mistral 7B (local, free)
- **Embeddings**: BAAI/bge-small-en-v1.5 (HuggingFace, free)
- **Vector DB**: ChromaDB
- **RAG Framework**: LlamaIndex
- **Evaluation**: RAGAS (faithfulness, relevancy, precision)
- **Backend**: FastAPI
- **Frontend**: React + Tailwind + Recharts
- **Container**: Docker

## Quick Start

```bash
# 1. Install Ollama and pull model
ollama pull mistral

# 2. Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. Frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

## Features
- Upload legal, medical, financial PDFs
- Ask domain-specific questions
- Auto-retrieval fallback when context is weak
- RAGAS evaluation: faithfulness, answer relevancy, context precision
- Live metrics dashboard with trend charts
