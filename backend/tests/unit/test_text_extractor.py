"""
Unit tests for the Text Extractor.
"""

import pytest

from app.rag.extractor import TextExtractor


@pytest.fixture
def extractor():
    return TextExtractor()


class TestPlainTextExtraction:
    """Test plain text file extraction."""

    def test_extracts_utf8_text(self, extractor):
        content = "Hello, this is a test document.\nWith multiple lines.".encode("utf-8")
        result = extractor.extract(content, "text/plain", "test.txt")
        assert "Hello" in result.text
        assert "multiple lines" in result.text
        assert result.pages == 1
        assert result.metadata["format"] == "text"

    def test_extracts_latin1_text(self, extractor):
        content = "Café résumé naïve".encode("latin-1")
        result = extractor.extract(content, "text/plain", "test.txt")
        assert "Caf" in result.text
        assert result.char_count > 0

    def test_counts_words(self, extractor):
        content = "one two three four five".encode("utf-8")
        result = extractor.extract(content, "text/plain", "test.txt")
        assert result.word_count == 5

    def test_includes_metadata(self, extractor):
        content = b"test content"
        result = extractor.extract(content, "text/plain", "myfile.txt")
        assert result.metadata["filename"] == "myfile.txt"
        assert result.metadata["content_type"] == "text/plain"
        assert result.metadata["original_size_bytes"] == len(content)


class TestPDFExtraction:
    """Test PDF extraction (requires pypdf)."""

    def test_rejects_invalid_pdf(self, extractor):
        """Invalid PDF bytes should raise an error."""
        content = b"not a pdf file"
        with pytest.raises(Exception):
            extractor.extract(content, "application/pdf", "bad.pdf")


class TestUnsupportedFormats:
    """Test handling of unsupported formats."""

    def test_rejects_unsupported_type(self, extractor):
        with pytest.raises(ValueError, match="Unsupported content type"):
            extractor.extract(b"data", "image/png", "image.png")

    def test_rejects_unknown_type(self, extractor):
        with pytest.raises(ValueError):
            extractor.extract(b"data", "application/octet-stream", "file.bin")
