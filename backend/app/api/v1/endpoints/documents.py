"""
Document upload and RAG query endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
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


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document for RAG processing.
    Supports PDF, TXT, DOCX formats.
    """
    # Validate file type
    allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # Validate file size (max 50MB)
    max_size = 50 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit",
        )

    doc_service = DocumentService(db)
    document = await doc_service.upload_and_process(
        user=current_user,
        filename=file.filename,
        content=content,
        content_type=file.content_type,
    )

    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's uploaded documents."""
    doc_service = DocumentService(db)
    documents = await doc_service.get_user_documents(current_user.id)
    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its embeddings."""
    doc_service = DocumentService(db)
    await doc_service.delete_document(document_id, current_user.id)


@router.post("/query", response_model=RAGQueryResponse)
async def query_documents(
    payload: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Query uploaded documents using RAG.
    Only searches documents owned by the current user.
    """
    doc_service = DocumentService(db)
    result = await doc_service.rag_query(
        user=current_user,
        query=payload.query,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
    )
    return result
