# ADR-001: FastAPI as Backend Framework

## Status: Accepted

## Context

SentinelAI requires a high-performance backend framework capable of handling concurrent AI model requests, WebSocket streaming, and real-time security analysis. The framework must support async I/O natively, provide automatic API documentation, and integrate well with Python's ML/AI ecosystem.

Key requirements:
- Async/await support for non-blocking I/O with multiple AI providers
- WebSocket support for real-time chat streaming
- Automatic OpenAPI documentation generation
- Strong type validation for request/response schemas
- High throughput under concurrent load
- Easy integration with SQLAlchemy, Redis, and AI libraries

## Decision

We chose **FastAPI** as the backend framework for SentinelAI.

Key factors:
1. **Native async support** — Built on Starlette and ASGI, FastAPI handles concurrent requests efficiently without blocking, critical for AI provider calls that have variable latency.
2. **Pydantic integration** — Automatic request validation and serialization with Python type hints reduces boilerplate and catches errors at the API boundary.
3. **OpenAPI auto-generation** — Interactive docs (Swagger UI, ReDoc) are generated automatically from code, keeping documentation always in sync.
4. **Performance** — Benchmarks place FastAPI among the fastest Python web frameworks, comparable to Node.js and Go for I/O-bound workloads.
5. **WebSocket support** — First-class WebSocket handling for streaming chat tokens.
6. **Dependency injection** — Clean DI system for managing database sessions, auth, and service dependencies.

## Consequences

**Positive:**
- Reduced development time through automatic validation and documentation
- Strong typing catches bugs at development time
- Async architecture handles AI provider latency gracefully
- Large ecosystem of compatible middleware and extensions
- Easy to onboard Python developers

**Negative:**
- Python's GIL limits CPU-bound parallelism (mitigated by offloading to worker processes)
- Smaller ecosystem than Django for traditional web features (admin panels, ORM migrations)
- Async complexity can introduce subtle bugs with database sessions

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Django + DRF** | Sync-first architecture would bottleneck on AI provider calls; heavier ORM not needed |
| **Flask** | No native async support; lacks built-in validation and OpenAPI generation |
| **Express.js (Node)** | Would fragment the team across Python (ML) and Node (API); lose access to Python AI libraries |
| **Go (Gin/Fiber)** | Excellent performance but poor integration with Python ML ecosystem; higher development cost |
