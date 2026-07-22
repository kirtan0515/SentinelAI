# ADR-001: FastAPI for backend

**Status:** Accepted

**Context:** Need async Python framework for handling concurrent LLM API calls + WebSocket streaming. Also want auto-generated API docs and Pydantic validation.

**Decision:** FastAPI. Native async, Pydantic baked in, auto OpenAPI docs, fast enough for I/O-bound work.

**Tradeoffs:**
- GIL is fine since we're I/O-bound (waiting on LLM APIs), not CPU-bound
- Less batteries-included than Django, but we don't need Django's admin/template system
- Async SQLAlchemy sessions can be tricky (solved with proper dependency injection)

**Rejected:**
- Django/DRF — sync-first, would block on LLM calls
- Flask — no async, no validation, would need too many extensions
- Node/Express — splits the stack, lose Python ML ecosystem access
