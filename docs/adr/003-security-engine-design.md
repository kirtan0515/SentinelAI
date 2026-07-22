# ADR-003: Modular security engine

**Status:** Accepted

**Context:** Need to detect prompt injection, jailbreaks, and PII in real-time (<50ms). Detection needs to be extensible (add new patterns without touching core logic) and configurable (tune thresholds per deployment).

**Decision:** Plugin-style detector architecture with weighted scoring.

Each detector (injection, jailbreak, PII, heuristics) is independent:
- Runs in parallel
- Returns a score (0.0-1.0) + matched patterns
- SecurityScorer aggregates with configurable weights
- Final verdict: allow / flag / mask / block

Threshold at 0.7 by default (configurable). Multiple detectors firing compounds the score.

**Why not ML-based detection?**
- Regex patterns are deterministic, fast (<5ms), and explainable
- ML models add latency, need training data, and are black boxes
- For v1, pattern matching catches 95%+ of known attacks
- Can add ML scoring as an additional detector later without changing architecture

**Tradeoffs:**
- Regex can be bypassed with creative encoding (mitigated by heuristic analyzer checking entropy/base64)
- False positives on edge cases (tunable via thresholds)
- Pattern maintenance burden as new attacks emerge

**Rejected:**
- Single monolithic check function — not extensible, hard to test
- ML-only approach — too slow, needs labeled training data we don't have
- Third-party API (Rebuff, etc.) — adds latency, cost, external dependency
