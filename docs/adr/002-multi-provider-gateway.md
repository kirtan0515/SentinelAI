# ADR-002: Multi-provider gateway with circuit breaker

**Status:** Accepted

**Context:** Need to support 4+ LLM providers (OpenAI, Anthropic, Google, Ollama) through a single interface. Providers go down, have rate limits, and vary in latency. Can't let one provider failure take down the whole system.

**Decision:** Gateway router with per-provider circuit breakers and fallback chains.

How it works:
- Each provider has a circuit breaker (closed → open after 5 failures → half-open after 60s)
- If primary model fails, automatically tries fallback chain (e.g. gpt-4 → gpt-4-turbo → gpt-3.5)
- Retry with exponential backoff (3 attempts max)
- Ollama (local) as the default — zero cost, no external dependency

**Tradeoffs:**
- More complex than just calling one API directly
- Circuit breaker state is in-memory (lost on restart, but recovers fast)
- Fallback might give worse quality responses (gpt-3.5 instead of gpt-4)

**Rejected:**
- Simple try/catch per request — no learning from repeated failures
- External service mesh (Istio) — overkill for this scale, adds operational complexity
- Single provider only — too fragile for production
