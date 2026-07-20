# ADR-004: RAG Implementation with pgvector

## Status: Accepted

## Context

SentinelAI provides Retrieval-Augmented Generation (RAG) to allow users to chat with their uploaded documents. We need a vector storage solution for document embeddings that supports:

- Similarity search with configurable distance metrics
- Access control (users should only query their own documents)
- Integration with our existing PostgreSQL database
- Reasonable performance at our expected scale (thousands of documents, millions of chunks)
- ACID transactions alongside relational data

## Decision

We chose **pgvector** (PostgreSQL extension) as our vector store, integrated directly with our existing PostgreSQL instance.

### Architecture

```
Document Upload → Chunking → Embedding (OpenAI) → pgvector Storage
                                                        ↓
User Query → Embed Query → Cosine Similarity Search → Context Assembly → LLM
```

### Key design choices:

1. **pgvector over dedicated vector DBs** — Single database for both relational and vector data eliminates sync issues and simplifies access control.

2. **Row-level access control** — Document chunks are linked to users via `document_id → documents.user_id`. Queries filter by user ownership at the SQL level, preventing cross-tenant data leakage.

3. **Chunking strategy:**
   - Chunk size: 512 tokens with 50-token overlap
   - Chunking method: Recursive text splitter respecting paragraph/sentence boundaries
   - Metadata preserved: page number, section header, source document

4. **Embedding model:** OpenAI `text-embedding-3-small` (1536 dimensions) — good balance of quality, cost, and speed.

5. **Index type:** HNSW (Hierarchical Navigable Small World) for approximate nearest neighbor search with `vector_cosine_ops`.

6. **Hybrid search:** Combine vector similarity with keyword matching (pg_trgm) for better recall on exact terms.

## Consequences

**Positive:**
- No additional infrastructure to manage (reuses existing PostgreSQL)
- ACID compliance — embeddings are transactionally consistent with metadata
- Native SQL joins enable complex queries (filter by date, document type, user)
- Access control is enforced at the database layer, not application layer
- Simplified backup and disaster recovery (single database)
- Cost effective — no additional SaaS fees for vector storage

**Negative:**
- pgvector performance degrades beyond ~10M vectors (acceptable for our scale)
- HNSW index rebuild on large inserts can be slow
- PostgreSQL becomes a more critical single point of failure
- Less sophisticated vector search features compared to dedicated solutions
- Embedding dimension changes require table migration

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Pinecone** | SaaS vendor lock-in; data leaves our infrastructure; per-query pricing at scale; access control requires complex metadata filtering |
| **Weaviate** | Additional infrastructure to manage; separate backup strategy; overkill for our scale |
| **ChromaDB** | Primarily for prototyping; lacks production-grade durability and access control |
| **Qdrant** | Strong technical option but adds operational complexity; separate scaling concerns |
| **Elasticsearch with dense vectors** | Heavy resource footprint; complex cluster management; not optimized for high-dimensional vectors |
