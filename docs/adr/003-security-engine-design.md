# ADR-003: Modular Security Engine Design

## Status: Accepted

## Context

SentinelAI's core value proposition is protecting LLM applications from adversarial attacks. The security landscape for LLMs evolves rapidly — new attack vectors (prompt injection, jailbreaks, data exfiltration, indirect injection) emerge frequently. We need a security architecture that:

- Detects multiple attack categories simultaneously
- Can be updated without redeploying the entire application
- Provides confidence scores rather than binary pass/fail
- Supports defense in depth (multiple detection layers)
- Maintains low latency to avoid degrading chat UX
- Generates audit trails for compliance

## Decision

We implement a **modular detector architecture** with a **scoring system** and **defense in depth** strategy.

### Architecture

```
Input → [Pre-processing] → [Detector Pipeline] → [Scoring Engine] → [Decision] → Output
                                    ↓
                            [Audit Logger]
```

### Components

1. **Detector Pipeline** — Pluggable detectors run in parallel:
   - `PromptInjectionDetector` — Pattern matching + ML classification
   - `JailbreakDetector` — Role-play and constraint bypass detection
   - `DataLeakageDetector` — PII/secrets detection in outputs
   - `ToxicityDetector` — Harmful content classification
   - `TopicGuardrail` — Off-topic request filtering

2. **Scoring Engine** — Aggregates detector results into a unified security score (0.0–1.0):
   - Weighted combination of detector confidence scores
   - Configurable thresholds per deployment
   - Historical context awareness (repeated low-score attempts)

3. **Defense in Depth** — Three security layers:
   - **Layer 1: Input validation** — Pre-processing sanitization and pattern detection
   - **Layer 2: Contextual analysis** — NeMo Guardrails for conversation-level threats
   - **Layer 3: Output filtering** — Post-generation PII masking and content validation

4. **Decision Engine** — Based on aggregate score:
   - Score > 0.8 → Allow (log only)
   - Score 0.5–0.8 → Flag for review (allow with warning)
   - Score < 0.5 → Block (return security error)

### Configuration
Detectors are configured via YAML, allowing runtime tuning without code changes.

## Consequences

**Positive:**
- New detectors can be added without modifying existing code
- Parallel execution keeps latency bounded
- Scoring system avoids false-positive hard blocks
- Audit trail supports compliance (SOC2, HIPAA)
- Defense in depth catches attacks that bypass individual detectors

**Negative:**
- Multiple detectors increase compute cost per request
- Score calibration requires ongoing tuning with real attack data
- Complex interaction between detectors can produce unexpected aggregate scores
- ML-based detectors require model updates as attacks evolve

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Single regex-based filter** | Too brittle; trivially bypassed by encoding tricks |
| **External WAF only** | WAFs don't understand LLM-specific attacks (semantic injection) |
| **LLM-as-judge (self-evaluation)** | Adds latency; vulnerable to the same attacks it's judging |
| **Binary allow/block** | Too many false positives; degrades user experience |
| **NeMo Guardrails only** | Good for conversation flow but lacks fine-grained scoring and custom detectors |
