"""RAG pipeline — query embeddings, retrieve chunks, generate answer with sources."""

from typing import Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorSearchResult, VectorStore
from app.services.model_router import ModelRouter

logger = structlog.get_logger(__name__)

# RAG prompt template
RAG_SYSTEM_PROMPT = """You are SentinelAI, a helpful AI assistant with access to the user's uploaded documents.
Answer questions based on the provided context from their documents.
If the context doesn't contain relevant information, say so clearly.
Always cite which document/section your answer comes from.
Never make up information that isn't in the provided context."""

RAG_CONTEXT_TEMPLATE = """Context from user's documents:
---
{context}
---

Based on the above context, please answer the following question:
{question}

If the context doesn't contain enough information to fully answer the question, 
say what you can determine from the context and note what's missing."""


class RAGPipeline:
    """
    Complete RAG pipeline with access-controlled retrieval.

    Security:
    - Only retrieves from documents owned by the requesting user
    - Queries pass through security engine before processing
    - Responses are filtered before returning
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(db)
        self.model_router = ModelRouter()

    async def query(
        self,
        user_id: UUID,
        question: str,
        document_ids: Optional[List[UUID]] = None,
        top_k: int = 5,
        model: str = "gpt-4",
    ) -> Dict:
        """
        Execute a RAG query.

        Steps:
        1. Generate embedding for the question
        2. Retrieve relevant chunks (user-scoped)
        3. Assemble context
        4. Query LLM with context
        5. Return answer with sources

        Args:
            user_id: ID of the requesting user (access control)
            question: User's question
            document_ids: Optional filter to specific documents
            top_k: Number of chunks to retrieve
            model: LLM model to use for generation

        Returns:
            Dict with answer, sources, model, tokens_used
        """
        # Step 1: Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(question)

        # Step 2: Retrieve relevant chunks
        search_results = await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        if not search_results:
            return {
                "answer": "I couldn't find relevant information in your documents "
                "to answer this question. Please make sure you've uploaded "
                "documents related to your query.",
                "sources": [],
                "model": model,
                "tokens_used": 0,
                "chunks_retrieved": 0,
            }

        # Step 3: Assemble context
        context = self._assemble_context(search_results)

        # Step 4: Query LLM
        prompt = RAG_CONTEXT_TEMPLATE.format(
            context=context,
            question=question,
        )

        llm_response = await self.model_router.route(
            model=model,
            message=prompt,
            system_prompt=RAG_SYSTEM_PROMPT,
        )

        # Step 5: Build response with sources
        sources = self._build_sources(search_results)

        return {
            "answer": llm_response.get("content", "Unable to generate response."),
            "sources": sources,
            "model": llm_response.get("model", model),
            "tokens_used": llm_response.get("tokens_used", 0),
            "chunks_retrieved": len(search_results),
            "cost_estimate": llm_response.get("cost_estimate", 0.0),
        }

    def _assemble_context(self, results: List[VectorSearchResult]) -> str:
        """
        Assemble context from search results.

        Formats each chunk with its source metadata
        for clear attribution in the LLM prompt.
        """
        context_parts: List[str] = []

        for i, result in enumerate(results, 1):
            source_info = f"[Source {i}]"
            if result.metadata.get("filename"):
                source_info = f"[Source {i}: {result.metadata['filename']}]"

            context_parts.append(
                f"{source_info} (Relevance: {result.similarity:.2f})\n"
                f"{result.content}"
            )

        return "\n\n".join(context_parts)

    def _build_sources(self, results: List[VectorSearchResult]) -> List[Dict]:
        """Build source citation list from search results."""
        sources: List[Dict] = []
        seen_documents = set()

        for result in results:
            source = {
                "document_id": str(result.document_id),
                "chunk_index": result.chunk_index,
                "similarity": round(result.similarity, 4),
                "preview": result.content[:200] + "..."
                if len(result.content) > 200
                else result.content,
            }

            # Add filename if available
            if result.metadata.get("filename"):
                source["filename"] = result.metadata["filename"]

            sources.append(source)
            seen_documents.add(result.document_id)

        return sources
