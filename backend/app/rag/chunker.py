"""
Document Chunker

Splits extracted text into overlapping chunks for embedding.
Uses recursive character splitting with configurable chunk sizes.
"""

import re
from dataclasses import dataclass, field
from typing import List

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Chunk:
    """A single chunk of text from a document."""

    content: str
    index: int
    start_char: int = 0
    end_char: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def word_count(self) -> int:
        return len(self.content.split())

    @property
    def char_count(self) -> int:
        return len(self.content)


class DocumentChunker:
    """
    Recursive character text splitter with overlap.

    Strategy:
    1. Try to split on paragraph boundaries (\n\n)
    2. If chunks are too large, split on sentence boundaries (. ! ?)
    3. If still too large, split on word boundaries
    4. Apply overlap to maintain context continuity

    Parameters:
    - chunk_size: Target size in characters per chunk (default 1000)
    - chunk_overlap: Number of overlapping characters (default 200)
    - min_chunk_size: Minimum chunk size to keep (default 50)
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Separators in priority order
        self._separators = [
            "\n\n",  # Paragraph breaks
            "\n",  # Line breaks
            ". ",  # Sentences
            "! ",
            "? ",
            "; ",  # Clauses
            ", ",  # Phrases
            " ",  # Words
        ]

    def chunk(self, text: str, metadata: dict = None) -> List[Chunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full document text
            metadata: Additional metadata to attach to each chunk

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        # Clean text
        text = self._clean_text(text)

        # Split recursively
        raw_chunks = self._recursive_split(text, self._separators)

        # Merge small chunks and apply overlap
        merged = self._merge_with_overlap(raw_chunks)

        # Create Chunk objects
        chunks: List[Chunk] = []
        char_offset = 0

        for i, content in enumerate(merged):
            if len(content.strip()) < self.min_chunk_size:
                continue

            chunk = Chunk(
                content=content.strip(),
                index=i,
                start_char=char_offset,
                end_char=char_offset + len(content),
                metadata=metadata or {},
            )
            chunks.append(chunk)
            char_offset += len(content) - self.chunk_overlap

        logger.info(
            "Document chunked",
            total_chars=len(text),
            num_chunks=len(chunks),
            avg_chunk_size=len(text) // max(len(chunks), 1),
        )

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Replace multiple newlines with double
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Replace multiple spaces with single
        text = re.sub(r" {2,}", " ", text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text using separators in priority order.
        """
        if len(text) <= self.chunk_size:
            return [text]

        # Find the best separator that actually exists in the text
        separator = None
        for sep in separators:
            if sep in text:
                separator = sep
                break

        if separator is None:
            # No separator found, force split at chunk_size
            return self._force_split(text)

        # Split on the separator
        parts = text.split(separator)
        result: List[str] = []
        current = ""

        for part in parts:
            # Check if adding this part exceeds chunk size
            test_content = current + separator + part if current else part

            if len(test_content) <= self.chunk_size:
                current = test_content
            else:
                # Save current chunk if non-empty
                if current:
                    result.append(current)
                # If the part itself is too large, split it further
                if len(part) > self.chunk_size:
                    # Use next separator level
                    remaining_seps = separators[separators.index(separator) + 1 :]
                    if remaining_seps:
                        sub_parts = self._recursive_split(part, remaining_seps)
                        result.extend(sub_parts)
                    else:
                        result.extend(self._force_split(part))
                    current = ""
                else:
                    current = part

        if current:
            result.append(current)

        return result

    def _force_split(self, text: str) -> List[str]:
        """Force split text at chunk_size boundaries (word-aware)."""
        chunks: List[str] = []
        while len(text) > self.chunk_size:
            # Find the last space within chunk_size
            split_point = text.rfind(" ", 0, self.chunk_size)
            if split_point == -1:
                split_point = self.chunk_size

            chunks.append(text[:split_point])
            text = text[split_point:].lstrip()

        if text:
            chunks.append(text)

        return chunks

    def _merge_with_overlap(self, chunks: List[str]) -> List[str]:
        """Apply overlap between consecutive chunks."""
        if not chunks or self.chunk_overlap == 0:
            return chunks

        result: List[str] = []

        for i, chunk in enumerate(chunks):
            if i == 0:
                result.append(chunk)
            else:
                # Get overlap from previous chunk
                prev = chunks[i - 1]
                overlap_text = prev[-self.chunk_overlap :] if len(prev) > self.chunk_overlap else ""

                # Only add overlap if it doesn't make chunk too large
                if overlap_text and len(overlap_text + chunk) <= self.chunk_size * 1.5:
                    # Find a clean break point in the overlap
                    break_point = overlap_text.rfind(" ")
                    if break_point > 0:
                        overlap_text = overlap_text[break_point + 1 :]

                    result.append(overlap_text + " " + chunk)
                else:
                    result.append(chunk)

        return result
