import os
import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional

from app.config import settings
from app.services.rag_service import rag_service
from app.models.schemas import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Form(default="rag_documents"),
):
    """
    Upload a PDF document and index it into ChromaDB.
    
    1. Validate file is PDF and not too large
    2. Save to disk
    3. Process: extract text → chunk → embed → store in ChromaDB
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )
    
    # Check file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB."
        )
    
    # Save file to disk
    upload_path = Path(settings.UPLOAD_DIR) / file.filename
    with open(upload_path, "wb") as f:
        f.write(contents)
    
    logger.info(f"Saved file: {upload_path} ({size_mb:.2f} MB)")
    
    try:
        # Process and index the PDF
        chunks_created = await rag_service.process_pdf(
            file_path=str(upload_path),
            collection_name=collection_name,
        )
        
        return UploadResponse(
            message=f"Successfully processed '{file.filename}'",
            file_name=file.filename,
            chunks_created=chunks_created,
            collection_name=collection_name,
        )
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        # Clean up file if processing failed
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )