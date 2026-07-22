"""Embedding service — generates vectors using Ollama (free) with OpenAI fallback."""

import asyncio
from typing import List

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Ollama embedding config (FREE, local)
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_EMBEDDING_DIMENSION = 768

# OpenAI embedding config (paid, optional fallback)
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
OPENAI_EMBEDDING_DIMENSION = 1536

# Use Ollama by default (free). Only use OpenAI if key is set AND ollama fails.
EMBEDDING_DIMENSION = OLLAMA_EMBEDDING_DIMENSION
MAX_BATCH_SIZE = 50
MAX_TEXT_LENGTH = 8000  # characters


class EmbeddingService:
    """
    Generates text embeddings locally using Ollama (free).

    Priority:
    1. Ollama (local, free) — uses nomic-embed-text model
    2. OpenAI (paid) — only if OPENAI_API_KEY is set and Ollama unavailable

    Before first use, pull the embedding model:
        ollama pull nomic-embed-text
    """

    def __init__(self):
        self._ollama_url = settings.OLLAMA_HOST
        self._use_openai_fallback = bool(settings.OPENAI_API_KEY)

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Returns:
            List of floats (768 dimensions with Ollama, 1536 with OpenAI)
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Uses Ollama locally (free). Falls back to OpenAI if configured.
        """
        if not texts:
            return []

        cleaned_texts = [self._prepare_text(t) for t in texts]

        # Try Ollama first (free)
        try:
            embeddings = await self._embed_with_ollama(cleaned_texts)
            return embeddings
        except Exception as e:
            logger.warning("Ollama embedding failed, checking fallback", error=str(e))

        # Fallback to OpenAI if API key is set
        if self._use_openai_fallback:
            try:
                embeddings = await self._embed_with_openai(cleaned_texts)
                return embeddings
            except Exception as e:
                logger.error("OpenAI embedding also failed", error=str(e))

        # Last resort: return zero vectors
        logger.error("All embedding providers failed, returning zero vectors")
        return [[0.0] * EMBEDDING_DIMENSION for _ in cleaned_texts]

    async def _embed_with_ollama(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama (free, local)."""
        embeddings: List[List[float]] = []

        async with httpx.AsyncClient() as client:
            for i, text in enumerate(texts):
                response = await client.post(
                    f"{self._ollama_url}/api/embeddings",
                    json={
                        "model": OLLAMA_EMBEDDING_MODEL,
                        "prompt": text,
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    raise Exception(
                        f"Ollama embedding failed: {response.status_code} - {response.text}"
                    )

                data = response.json()
                embedding = data.get("embedding", [])

                if not embedding:
                    raise Exception("Ollama returned empty embedding")

                embeddings.append(embedding)

                if (i + 1) % 10 == 0:
                    logger.debug(
                        "Ollama embeddings progress",
                        completed=i + 1,
                        total=len(texts),
                    )

        logger.info(
            "Ollama embeddings generated",
            count=len(embeddings),
            dimension=len(embeddings[0]) if embeddings else 0,
        )
        return embeddings

    async def _embed_with_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API (paid fallback)."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        all_embeddings: List[List[float]] = []

        batches = self._create_batches(texts, MAX_BATCH_SIZE)
        for batch in batches:
            response = await client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=batch,
            )
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([item.embedding for item in sorted_data])

        return all_embeddings

    def _prepare_text(self, text: str) -> str:
        """Clean and truncate text for embedding."""
        text = " ".join(text.split())
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        return text

    def _create_batches(self, items: List, batch_size: int) -> List[List]:
        """Split items into batches."""
        return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    @staticmethod
    def get_dimension() -> int:
        """Get the embedding dimension."""
        return EMBEDDING_DIMENSION
