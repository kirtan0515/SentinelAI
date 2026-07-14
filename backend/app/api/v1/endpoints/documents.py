"""
Document upload and RAG query endpoints.

Provides:
- Document upload with automatic processing (extract → chunk → embed)
- Document listing and management
- RAG queries with access-controlled retrieval
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentListResponse,
    DocumentUploadResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.services.document_service import DocumentService

router = APIRouter()

# Allowed MIME types for upload
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document for RAG processing.

    The document will be automatically processed:
    1. Text extracted (PDF, TXT, DOCX)
    2. Split into chunks with overlap
    3. Embeddings generated via OpenAI
    4. Stored in pgvector for similarity search

    Supported formats: PDF, TXT, DOCX
    Maximum file size: 50MB
    """
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. "
            f"Supported: {list(ALLOWED_TYPES.values())}",
        )

    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size ({len(content) / 1024 / 1024:.1f}MB) "
            f"exceeds {MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    doc_service = DocumentService(db)
    document = await doc_service.upload_and_process(
        user=current_user,
        filename=file.filename or "unnamed",
        content=content,
        content_type=file.content_type,
    )

    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """
    List user's uploaded documents.
    Optionally filter by status (processing, ready, failed).
    """
    doc_service = DocumentService(db)
    documents = await doc_service.get_user_documents(current_user.id)

    # Apply status filter
    if status_filter:
        documents = [d for d in documents if d.status == status_filter]

    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=DocumentUploadResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document's details."""
    doc_service = DocumentService(db)
    document = await doc_service.get_document(document_id, current_user.id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )

    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        status=document.status,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a document and all its embeddings.
    Only the document owner can delete.
    """
    doc_service = DocumentService(db)
    deleted = await doc_service.delete_document(document_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )


@router.post("/query", response_model=RAGQueryResponse)
async def query_documents(
    payload: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Query uploaded documents using RAG.

    How it works:
    1. Your question is converted to a vector embedding
    2. Similar chunks are retrieved from your documents
    3. The LLM answers based on the retrieved context
    4. Sources are cited in the response

    Access Control:
    - Only searches documents YOU own
    - Other users' documents are never accessible

    Parameters:
    - query: Your question in natural language
    - document_ids: (optional) Filter to specific documents
    - top_k: Number of chunks to retrieve (default 5, max 20)
    """
    if payload.top_k > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="top_k cannot exceed 20",
        )

    doc_service = DocumentService(db)
    result = await doc_service.rag_query(
        user=current_user,
        query=payload.query,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
    )
    return result
