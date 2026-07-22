# ADR-004: pgvector for RAG instead of dedicated vector DB

**Status:** Accepted

**Context:** Need vector storage for document embeddings (RAG). Options: Pinecone, Weaviate, Qdrant, Milvus, or just pgvector in our existing PostgreSQL.

**Decision:** pgvector extension in PostgreSQL.

Reasoning:
- Already running PostgreSQL for everything else — no additional service to operate
- HNSW index gives good enough performance for our scale (<1M vectors)
- Access control is trivial (JOIN with documents table WHERE user_id = ?)
- Transactions across relational + vector data in one DB
- Free, no vendor lock-in

**Tradeoffs:**
- Slower than purpose-built vector DBs at very large scale (>10M vectors)
- No built-in filtering/metadata indexing (handled in SQL WHERE clause)
- HNSW index rebuild on large inserts can be slow

**When to switch:** If we hit >5M vectors and search latency exceeds 100ms p99, evaluate Qdrant or Pinecone. The vector_store.py abstraction makes swapping straightforward.

**Rejected:**
- Pinecone — managed service, costs money, vendor lock-in
- Weaviate/Qdrant — great but adds another service to deploy and monitor
- ChromaDB — not production-ready, no real persistence guarantees
