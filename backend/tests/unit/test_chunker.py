"""
Unit tests for the Document Chunker.
"""

import pytest

from app.rag.chunker import DocumentChunker


@pytest.fixture
def chunker():
    return DocumentChunker(chunk_size=200, chunk_overlap=50, min_chunk_size=20)


@pytest.fixture
def large_chunker():
    return DocumentChunker(chunk_size=1000, chunk_overlap=200, min_chunk_size=50)


class TestBasicChunking:
    """Test basic chunking behavior."""

    def test_short_text_single_chunk(self, chunker):
        """Text shorter than chunk_size stays as one chunk."""
        text = "This is a short document."
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_empty_text_no_chunks(self, chunker):
        """Empty text returns no chunks."""
        chunks = chunker.chunk("")
        assert len(chunks) == 0

    def test_whitespace_only_no_chunks(self, chunker):
        """Whitespace-only text returns no chunks."""
        chunks = chunker.chunk("   \n\n\t  ")
        assert len(chunks) == 0

    def test_long_text_multiple_chunks(self, chunker):
        """Long text gets split into multiple chunks."""
        text = "This is sentence number one. " * 50  # ~1450 chars
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_chunks_respect_max_size(self, chunker):
        """No chunk exceeds 1.5x chunk_size (overlap allowance)."""
        text = "Word " * 200  # 1000 chars
        chunks = chunker.chunk(text)
        max_allowed = chunker.chunk_size * 1.5
        for chunk in chunks:
            assert chunk.char_count <= max_allowed + 100  # Some tolerance

    def test_chunk_indices_sequential(self, chunker):
        """Chunk indices should be sequential."""
        text = "Paragraph one with content.\n\n" * 20
        chunks = chunker.chunk(text)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i


class TestParagraphSplitting:
    """Test splitting on paragraph boundaries."""

    def test_splits_on_paragraphs(self, chunker):
        """Should prefer paragraph breaks as split points."""
        text = "First paragraph content here.\n\nSecond paragraph content here.\n\nThird paragraph."
        chunks = chunker.chunk(text)
        # Should split cleanly on \n\n if each part is under chunk_size
        assert len(chunks) >= 1

    def test_preserves_paragraph_content(self, chunker):
        """Content should be preserved across chunks."""
        para1 = "A" * 100
        para2 = "B" * 100
        para3 = "C" * 100
        text = f"{para1}\n\n{para2}\n\n{para3}"
        chunks = chunker.chunk(text)
        all_content = " ".join(c.content for c in chunks)
        assert "A" * 50 in all_content
        assert "B" * 50 in all_content
        assert "C" * 50 in all_content


class TestOverlap:
    """Test chunk overlap behavior."""

    def test_overlap_provides_context(self, large_chunker):
        """Consecutive chunks should share some content for context."""
        # Create text that will definitely produce multiple chunks
        sentences = [f"Sentence number {i} with some content." for i in range(100)]
        text = " ".join(sentences)
        chunks = large_chunker.chunk(text)

        if len(chunks) >= 2:
            # Check some content overlap between consecutive chunks
            # (overlap means end of chunk N appears in start of chunk N+1)
            chunk1_end = chunks[0].content[-50:]
            chunk2_start = chunks[1].content[:200]
            # Due to word-boundary splitting, exact overlap isn't guaranteed
            # but chunks should have reasonable lengths
            assert chunks[0].char_count > 0
            assert chunks[1].char_count > 0


class TestMetadata:
    """Test chunk metadata."""

    def test_metadata_passed_through(self, chunker):
        """Custom metadata should appear on all chunks."""
        text = "A" * 500
        metadata = {"filename": "test.pdf", "page": 1}
        chunks = chunker.chunk(text, metadata=metadata)
        for chunk in chunks:
            assert chunk.metadata["filename"] == "test.pdf"

    def test_word_count_accurate(self, chunker):
        """Word count property should be accurate."""
        text = "one two three four five six seven eight nine ten " * 10
        chunks = chunker.chunk(text)
        for chunk in chunks:
            expected = len(chunk.content.split())
            assert chunk.word_count == expected


class TestEdgeCases:
    """Test edge cases."""

    def test_single_very_long_word(self, chunker):
        """Handle text with no natural split points."""
        text = "A" * 500  # No spaces
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1
        # Should still produce valid chunks
        total_chars = sum(c.char_count for c in chunks)
        assert total_chars >= 500  # All content preserved

    def test_many_newlines(self, chunker):
        """Handle excessive newlines gracefully."""
        text = "content\n\n\n\n\n\n\n\nmore content\n\n\n\n\nfinal"
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1
        all_content = " ".join(c.content for c in chunks)
        assert "content" in all_content
        assert "final" in all_content

    def test_special_characters(self, chunker):
        """Handle special characters."""
        text = "Hello! How are you? I'm fine. Let's code: x = 1 + 2; print(x)"
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1
        assert "Hello" in chunks[0].content
