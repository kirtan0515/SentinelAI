# ADR-002: Unified Multi-Provider Gateway with Circuit Breaker

## Status: Accepted

## Context

SentinelAI must route requests to multiple AI providers (OpenAI, Anthropic, Google, Ollama) while maintaining high availability. Provider outages are common — OpenAI has experienced multiple incidents, and rate limits can temporarily block requests. We need a resilient routing layer that:

- Abstracts provider-specific APIs behind a unified interface
- Handles provider failures gracefully without cascading to users
- Supports automatic fallback when a provider is degraded
- Enforces rate limiting per user and per provider
- Enables easy addition of new providers

## Decision

We implement a **unified AI gateway** using the **circuit breaker pattern** with provider-specific adapters.

Architecture:
1. **Provider adapters** — Each AI provider (OpenAI, Anthropic, Google, Ollama) gets a dedicated adapter implementing a common interface (`BaseProvider`).
2. **Circuit breaker** — Each provider connection is wrapped in a circuit breaker that tracks failure rates and opens the circuit when a threshold is exceeded (5 failures in 60 seconds).
3. **Smart routing** — The gateway router selects providers based on model requested, fallback priority, and circuit state.
4. **Rate limiting** — Token bucket rate limiter per user, per provider, enforced at the gateway level.
5. **Request/response normalization** — All provider responses are normalized to a common schema before reaching the application layer.

Circuit breaker states:
- **Closed** — Normal operation, requests pass through
- **Open** — Provider failed, requests immediately fallback (60s timeout)
- **Half-open** — After timeout, allow one probe request to test recovery

## Consequences

**Positive:**
- Users experience minimal disruption during provider outages
- Adding new providers requires only implementing the adapter interface
- Circuit breaker prevents resource exhaustion from repeated failed calls
- Unified interface simplifies the chat and security layers
- Cost optimization by routing to cheapest available provider

**Negative:**
- Added complexity in the routing layer
- Circuit breaker state must be shared across instances (Redis-backed)
- Fallback models may have different capabilities than primary
- Response normalization may lose provider-specific features

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Direct provider calls** | No resilience; single provider failure breaks the entire system |
| **LiteLLM proxy** | External dependency; less control over security scanning integration |
| **AWS Bedrock only** | Vendor lock-in; doesn't support Ollama for local/air-gapped deployments |
| **Simple retry with exponential backoff** | Doesn't prevent thundering herd; slow recovery detection |
