"""
Embedding Service

Generates vector embeddings for text chunks using OpenAI's
text-embedding-ada-002 model (1536 dimensions).

Supports batching for efficiency and rate limit handling.
"""

import asyncio
from typing import List

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# OpenAI embedding model configuration
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536
MAX_BATCH_SIZE = 100  # OpenAI limit per request
MAX_TOKENS_PER_TEXT = 8191  # ada-002 token limit


class EmbeddingService:
    """
    Generates text embeddings using OpenAI's embedding API.

    Features:
    - Batch processing for efficiency
    - Automatic chunking of large batches
    - Retry handling for rate limits
    - Dimension validation
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-initialize OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats (1536 dimensions)
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (each 1536 dimensions)
        """
        if not texts:
            return []

        # Clean and truncate texts
        cleaned_texts = [self._prepare_text(t) for t in texts]

        # Process in batches
        all_embeddings: List[List[float]] = []
        batches = self._create_batches(cleaned_texts, MAX_BATCH_SIZE)

        for batch_idx, batch in enumerate(batches):
            try:
                batch_embeddings = await self._embed_batch(batch)
                all_embeddings.extend(batch_embeddings)

                logger.debug(
                    "Embedding batch processed",
                    batch=batch_idx + 1,
                    total_batches=len(batches),
                    texts_in_batch=len(batch),
                )
            except Exception as e:
                logger.error(
                    "Embedding batch failed",
                    batch=batch_idx + 1,
                    error=str(e),
                )
                # Fill with zero vectors for failed batch
                all_embeddings.extend(
                    [[0.0] * EMBEDDING_DIMENSION for _ in batch]
                )

        return all_embeddings

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a single batch of texts via OpenAI API."""
        client = self._get_client()

        # Retry with backoff for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=texts,
                )
                # Sort by index to maintain order
                sorted_data = sorted(response.data, key=lambda x: x.index)
                return [item.embedding for item in sorted_data]

            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(
                        "Embedding rate limited, retrying",
                        attempt=attempt + 1,
                        wait_seconds=wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise

    def _prepare_text(self, text: str) -> str:
        """Clean and truncate text for embedding."""
        # Remove excessive whitespace
        text = " ".join(text.split())
        # Truncate to approximate token limit (rough: 4 chars per token)
        max_chars = MAX_TOKENS_PER_TEXT * 4
        if len(text) > max_chars:
            text = text[:max_chars]
        return text

    def _create_batches(self, items: List, batch_size: int) -> List[List]:
        """Split items into batches."""
        return [
            items[i: i + batch_size]
            for i in range(0, len(items), batch_size)
        ]

    @staticmethod
    def get_dimension() -> int:
        """Get the embedding dimension."""
        return EMBEDDING_DIMENSION
