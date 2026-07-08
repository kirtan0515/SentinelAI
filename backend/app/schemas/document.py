"""
Document Pydantic schemas.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    id: UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for listing documents."""

    documents: list[DocumentUploadResponse]
    total: int


class RAGQueryRequest(BaseModel):
    """Schema for RAG query."""

    query: str
    document_ids: Optional[list[UUID]] = None
    top_k: int = 5


class RAGQueryResponse(BaseModel):
    """Schema for RAG query response."""

    answer: str
    sources: list[dict]
    model: str
    tokens_used: int
