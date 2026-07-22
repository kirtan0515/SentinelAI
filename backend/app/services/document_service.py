"""
Document Service - Orchestrates document upload, processing, and RAG queries.

Coordinates:
- Text extraction
- Chunking
- Embedding generation
- Vector storage
- RAG retrieval and generation
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.extractor import TextExtractor
from app.rag.pipeline import RAGPipeline
from app.rag.vector_store import VectorStore
from app.schemas.document import DocumentUploadResponse, RAGQueryResponse

logger = structlog.get_logger(__name__)


class DocumentService:
    """
    Manages document lifecycle and RAG pipeline.

    Flow:
    Upload → Extract → Chunk → Embed → Store → Ready for queries

    Access Control:
    - Users can only access their own documents
    - RAG queries are scoped to user's documents
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.extractor = TextExtractor()
        self.chunker = DocumentChunker(
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=50,
        )
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(db)

    async def upload_and_process(
        self,
        user: User,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> DocumentUploadResponse:
        """
        Upload and process a document through the full pipeline.

        Steps:
        1. Create document record (status: processing)
        2. Extract text from file
        3. Chunk the text
        4. Generate embeddings for all chunks
        5. Store chunks with embeddings in pgvector
        6. Update document status to ready
        """
        # Step 1: Create document record
        doc_id = uuid.uuid4()
        document = Document(
            id=doc_id,
            user_id=user.id,
            filename=filename,
            file_type=content_type,
            file_size=len(content),
            status="processing",
            chunk_count=0,
        )
        self.db.add(document)
        await self.db.flush()

        try:
            # Step 2: Extract text
            extraction = self.extractor.extract(
                content=content,
                content_type=content_type,
                filename=filename,
            )

            if not extraction.text.strip():
                await self._update_status(doc_id, "failed")
                return self._build_response(document)

            # Step 3: Chunk the text
            chunks = self.chunker.chunk(
                text=extraction.text,
                metadata={
                    "filename": filename,
                    "pages": extraction.pages,
                    "source_type": content_type,
                },
            )

            if not chunks:
                await self._update_status(doc_id, "failed")
                return self._build_response(document)

            # Step 4: Generate embeddings
            chunk_texts = [c.content for c in chunks]
            embeddings = await self.embedding_service.generate_embeddings(chunk_texts)

            # Step 5: Store chunks with embeddings
            chunk_data = [
                {
                    "content": chunk.content,
                    "index": chunk.index,
                    "embedding": embedding,
                    "metadata": {
                        "filename": filename,
                        "chunk_index": chunk.index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        "word_count": chunk.word_count,
                    },
                }
                for chunk, embedding in zip(chunks, embeddings)
            ]

            stored_count = await self.vector_store.store_chunks(
                document_id=doc_id,
                chunks=chunk_data,
            )

            # Step 6: Update document status
            await self._update_document(
                doc_id,
                status="ready",
                chunk_count=stored_count,
            )

            document.status = "ready"
            document.chunk_count = stored_count

            logger.info(
                "Document processed successfully",
                document_id=str(doc_id),
                filename=filename,
                chunks=stored_count,
                pages=extraction.pages,
            )

        except Exception as e:
            logger.error(
                "Document processing failed",
                document_id=str(doc_id),
                error=str(e),
            )
            await self._update_status(doc_id, "failed")
            document.status = "failed"

        return self._build_response(document)

    async def get_user_documents(self, user_id: UUID) -> List[DocumentUploadResponse]:
        """Get all documents for a user."""
        stmt = (
            select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        )
        result = await self.db.execute(stmt)
        documents = result.scalars().all()

        return [self._build_response(doc) for doc in documents]

    async def get_document(self, document_id: UUID, user_id: UUID) -> Optional[Document]:
        """Get a specific document (access controlled)."""
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        """
        Delete a document and all its chunks.
        Access controlled: only document owner can delete.
        """
        # Verify ownership
        document = await self.get_document(document_id, user_id)
        if not document:
            return False

        # Delete chunks first (cascade should handle but be explicit)
        await self.vector_store.delete_document_chunks(document_id)

        # Delete document
        stmt = delete(Document).where(Document.id == document_id)
        await self.db.execute(stmt)

        logger.info(
            "Document deleted",
            document_id=str(document_id),
            user_id=str(user_id),
        )
        return True

    async def rag_query(
        self,
        user: User,
        query: str,
        document_ids: Optional[List[UUID]] = None,
        top_k: int = 5,
        model: str = "gpt-4",
    ) -> RAGQueryResponse:
        """
        Query documents using RAG pipeline.

        Access Control:
        - Only searches user's own documents
        - Document IDs are validated against user ownership

        Args:
            user: Requesting user
            query: Natural language question
            document_ids: Optional filter to specific documents
            top_k: Number of chunks to retrieve
            model: LLM model for generation

        Returns:
            RAGQueryResponse with answer and source citations
        """
        # Validate document ownership if specific IDs provided
        if document_ids:
            valid_ids = await self._validate_document_access(document_ids, user.id)
            if not valid_ids:
                return RAGQueryResponse(
                    answer="None of the specified documents were found "
                    "or you don't have access to them.",
                    sources=[],
                    model=model,
                    tokens_used=0,
                )
            document_ids = valid_ids

        # Run RAG pipeline
        pipeline = RAGPipeline(self.db)
        result = await pipeline.query(
            user_id=user.id,
            question=query,
            document_ids=document_ids,
            top_k=top_k,
            model=model,
        )

        return RAGQueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            model=result["model"],
            tokens_used=result["tokens_used"],
        )

    async def _validate_document_access(
        self, document_ids: List[UUID], user_id: UUID
    ) -> List[UUID]:
        """Validate that all document IDs belong to the user."""
        stmt = select(Document.id).where(
            Document.id.in_(document_ids),
            Document.user_id == user_id,
            Document.status == "ready",
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def _update_status(self, document_id: UUID, status: str) -> None:
        """Update document status."""
        stmt = update(Document).where(Document.id == document_id).values(status=status)
        await self.db.execute(stmt)

    async def _update_document(self, document_id: UUID, **kwargs) -> None:
        """Update document fields."""
        stmt = update(Document).where(Document.id == document_id).values(**kwargs)
        await self.db.execute(stmt)

    def _build_response(self, document: Document) -> DocumentUploadResponse:
        """Build API response from document model."""
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            chunk_count=document.chunk_count,
            created_at=document.created_at,
        )
