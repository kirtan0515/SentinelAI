"""
SentinelAI RAG (Retrieval-Augmented Generation) System

Secure document processing pipeline:
1. Document Upload & Validation
2. Text Extraction (PDF, DOCX, TXT)
3. Intelligent Chunking (recursive, overlap)
4. Embedding Generation (OpenAI ada-002)
5. Vector Storage (pgvector)
6. Similarity Search (cosine distance)
7. Context Assembly & LLM Query
8. Access-Controlled Retrieval (user-scoped)
"""

# Lazy imports to avoid circular/heavy dependencies at module level
# Use: from app.rag.pipeline import RAGPipeline
# Use: from app.rag.chunker import DocumentChunker
# Use: from app.rag.embeddings import EmbeddingService
# Use: from app.rag.extractor import TextExtractor
