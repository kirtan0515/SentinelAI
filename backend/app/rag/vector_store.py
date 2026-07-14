"""
Vector Store

pgvector-backed vector storage and similarity search.
Provides CRUD operations for document embeddings with
access-controlled retrieval (user-scoped queries).
"""

import json
import uuid
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import structlog
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk

logger = structlog.get_logger(__name__)


class VectorSearchResult:
    """Result from a vector similarity search."""

    def __init__(
        self,
        chunk_id: UUID,
        document_id: UUID,
        content: str,
        similarity: float,
        chunk_index: int,
        metadata: Dict = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.content = content
        self.similarity = similarity
        self.chunk_index = chunk_index
        self.metadata = metadata or {}


class VectorStore:
    """
    pgvector-backed vector storage.

    Operations:
    - Store embeddings for document chunks
    - Similarity search with cosine distance
    - Access-controlled queries (filtered by user documents)
    - Batch operations for efficiency
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_chunks(
        self,
        document_id: UUID,
        chunks: List[Dict],
    ) -> int:
        """
        Store document chunks with embeddings.

        Args:
            document_id: Parent document ID
            chunks: List of dicts with keys: content, embedding, index, metadata

        Returns:
            Number of chunks stored
        """
        db_chunks = []
        for chunk_data in chunks:
            db_chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=document_id,
                content=chunk_data["content"],
                chunk_index=chunk_data["index"],
                embedding=chunk_data.get("embedding"),
                metadata_json=json.dumps(chunk_data.get("metadata", {})),
            )
            db_chunks.append(db_chunk)

        self.db.add_all(db_chunks)
        await self.db.flush()

        logger.info(
            "Chunks stored in vector store",
            document_id=str(document_id),
            count=len(db_chunks),
        )

        return len(db_chunks)

    async def similarity_search(
        self,
        query_embedding: List[float],
        user_id: UUID,
        document_ids: Optional[List[UUID]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[VectorSearchResult]:
        """
        Search for similar chunks using cosine distance.

        Access Control:
        - Only searches documents owned by the specified user
        - Optionally filtered to specific document IDs

        Args:
            query_embedding: Query vector (1536 dimensions)
            user_id: Owner user ID (access control)
            document_ids: Optional filter to specific documents
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of VectorSearchResult ordered by similarity (descending)
        """
        # Build the query with pgvector cosine distance
        # 1 - cosine_distance = cosine_similarity
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        # Base query: join chunks with documents for access control
        query = f"""
            SELECT 
                dc.id,
                dc.document_id,
                dc.content,
                dc.chunk_index,
                dc.metadata_json,
                1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.user_id = :user_id
              AND dc.embedding IS NOT NULL
              AND 1 - (dc.embedding <=> '{embedding_str}'::vector) > :threshold
        """

        params = {
            "user_id": str(user_id),
            "threshold": similarity_threshold,
        }

        # Filter by specific documents if provided
        if document_ids:
            doc_ids_str = ",".join(f"'{str(did)}'" for did in document_ids)
            query += f" AND dc.document_id IN ({doc_ids_str})"

        query += " ORDER BY similarity DESC LIMIT :top_k"
        params["top_k"] = top_k

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        results = []
        for row in rows:
            metadata = {}
            if row.metadata_json:
                try:
                    metadata = json.loads(row.metadata_json)
                except (json.JSONDecodeError, TypeError):
                    pass

            results.append(
                VectorSearchResult(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    content=row.content,
                    similarity=row.similarity,
                    chunk_index=row.chunk_index,
                    metadata=metadata,
                )
            )

        logger.info(
            "Similarity search completed",
            user_id=str(user_id),
            results=len(results),
            top_similarity=results[0].similarity if results else 0,
        )

        return results

    async def delete_document_chunks(self, document_id: UUID) -> int:
        """Delete all chunks for a document."""
        stmt = delete(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def get_chunk_count(self, document_id: UUID) -> int:
        """Get number of chunks for a document."""
        stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())
