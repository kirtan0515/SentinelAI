# SentinelAI — System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                              │
│                                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                      │
│   │   Browser    │    │  Mobile App  │    │  API Client  │                      │
│   │  (Next.js)   │    │   (Future)   │    │  (External)  │                      │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                      │
└──────────┼───────────────────┼───────────────────┼──────────────────────────────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                                            │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                     Next.js 14 (App Router)                              │   │
│   │                                                                          │   │
│   │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌───────────────┐  │   │
│   │  │ Landing │ │  Auth    │ │Dashboard │ │  Chat   │ │   Admin       │  │   │
│   │  │  Page   │ │Login/Reg │ │ + Charts │ │  + RAG  │ │ + Security    │  │   │
│   │  └─────────┘ └──────────┘ └──────────┘ └─────────┘ └───────────────┘  │   │
│   │                                                                          │   │
│   │  ┌──────────────────────────────────────────────────────────────────┐   │   │
│   │  │  Zustand (Auth Store) │ Axios (API Client) │ Recharts (Viz)     │   │   │
│   │  └──────────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │ REST + WebSocket
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY LAYER                                        │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                        FastAPI Application                                │   │
│   │                                                                          │   │
│   │  ┌────────────────────── MIDDLEWARE STACK ──────────────────────────┐   │   │
│   │  │                                                                   │   │   │
│   │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │   │   │
│   │  │  │    CORS      │  │   Security   │  │   Rate Limiter     │    │   │   │
│   │  │  │  Middleware   │  │   Headers    │  │ (Redis sliding     │    │   │   │
│   │  │  │              │  │ (HSTS, CSP)  │  │  window per-user)  │    │   │   │
│   │  │  └──────────────┘  └──────────────┘  └────────────────────┘    │   │   │
│   │  │                                                                   │   │   │
│   │  └───────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │  ┌────────────────────── API ROUTES ────────────────────────────────┐   │   │
│   │  │                                                                   │   │   │
│   │  │  /auth     /chat     /documents    /security    /admin    /audit  │   │   │
│   │  │  /models   /gateway  /ws/chat                                     │   │   │
│   │  │                                                                   │   │   │
│   │  └───────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │  ┌────────────────── DEPENDENCY INJECTION ──────────────────────────┐   │   │
│   │  │  get_db() │ get_current_user() │ get_current_admin()              │   │   │
│   │  └───────────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY ENGINE LAYER                                     │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                     SecurityEngine (Orchestrator)                          │   │
│   │                                                                          │   │
│   │  ┌───────────────────────── DETECTORS ─────────────────────────────┐   │   │
│   │  │                                                                  │   │   │
│   │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │   │   │
│   │  │  │   Prompt     │  │  Jailbreak   │  │   Sensitive Data     │ │   │   │
│   │  │  │  Injection   │  │  Detector    │  │     Detector         │ │   │   │
│   │  │  │  Detector    │  │              │  │                      │ │   │   │
│   │  │  │              │  │ • DAN attacks│  │ • Credit cards       │ │   │   │
│   │  │  │ • Override   │  │ • Bypass     │  │ • SSN, API keys      │ │   │   │
│   │  │  │ • Extraction │  │ • Roleplay   │  │ • Passwords          │ │   │   │
│   │  │  │ • Delimiter  │  │ • Hypothetic │  │ • Private keys       │ │   │   │
│   │  │  │ • Manipulate │  │ • Social eng │  │ • JWT, conn strings  │ │   │   │
│   │  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │   │   │
│   │  │                                                                  │   │   │
│   │  │  ┌──────────────┐  ┌──────────────────────────────────────────┐│   │   │
│   │  │  │  Heuristic   │  │          Response Filter                  ││   │   │
│   │  │  │  Analyzer    │  │                                           ││   │   │
│   │  │  │              │  │  • PII masking in output                  ││   │   │
│   │  │  │ • Entropy    │  │  • System prompt leak detection           ││   │   │
│   │  │  │ • Base64     │  │  • Harmful content flagging               ││   │   │
│   │  │  │ • Repetition │  │  • Length truncation                      ││   │   │
│   │  │  │ • Unicode    │  │                                           ││   │   │
│   │  │  └──────────────┘  └──────────────────────────────────────────┘│   │   │
│   │  └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │  ┌────────────────────── SCORING ───────────────────────────────────┐   │   │
│   │  │  SecurityScorer → Weighted aggregation → SecurityVerdict          │   │   │
│   │  │  (allow / flag / mask / block)                                    │   │   │
│   │  └──────────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AI GATEWAY LAYER                                          │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      GatewayRouter                                        │   │
│   │                                                                          │   │
│   │  ┌──────────────────── PROVIDERS ──────────────────────────────────┐   │   │
│   │  │                                                                  │   │   │
│   │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │   │   │
│   │  │  │  OpenAI  │  │Anthropic │  │  Google  │  │    Ollama    │  │   │   │
│   │  │  │  GPT-4   │  │  Claude  │  │  Gemini  │  │  Llama 3 ★  │  │   │   │
│   │  │  │  (paid)  │  │  (paid)  │  │  (paid)  │  │   (FREE)    │  │   │   │
│   │  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │   │   │
│   │  │                                                                  │   │   │
│   │  └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │  ┌─────────── RESILIENCE ──────────┐  ┌────────── FEATURES ──────────┐ │   │
│   │  │                                  │  │                              │ │   │
│   │  │  • Circuit Breaker (per provider)│  │  • Retry + exponential      │ │   │
│   │  │  • Fallback chains              │  │    backoff                   │ │   │
│   │  │  • Health monitoring            │  │  • Cost estimation           │ │   │
│   │  │                                  │  │  • Token counting            │ │   │
│   │  └──────────────────────────────────┘  └──────────────────────────────┘ │   │
│   │                                                                          │   │
│   │  ┌─────────── GUARDRAILS ──────────────────────────────────────────┐   │   │
│   │  │  NVIDIA NeMo Guardrails (optional)                                │   │   │
│   │  │  • Input rails (before LLM)                                       │   │   │
│   │  │  • Output rails (after LLM)                                       │   │   │
│   │  │  • Colang rule definitions                                        │   │   │
│   │  └──────────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          RAG PIPELINE                                             │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │  ┌───────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────────┐    │   │
│   │  │  Upload   │  │  Extract │  │    Chunk     │  │    Embed       │    │   │
│   │  │           │→ │          │→ │              │→ │                │    │   │
│   │  │ PDF/DOCX  │  │ pypdf    │  │ Recursive    │  │ Ollama         │    │   │
│   │  │ /TXT      │  │ python-  │  │ splitter     │  │ nomic-embed ★  │    │   │
│   │  │           │  │ docx     │  │ + overlap    │  │ (FREE, local)  │    │   │
│   │  └───────────┘  └──────────┘  └──────────────┘  └───────┬────────┘    │   │
│   │                                                           │             │   │
│   │                                                           ▼             │   │
│   │  ┌────────────────┐  ┌──────────────────────────────────────────┐     │   │
│   │  │  Query Flow    │  │             pgvector                      │     │   │
│   │  │                │  │                                           │     │   │
│   │  │ Question       │  │  • Cosine similarity search               │     │   │
│   │  │   ↓ embed      │  │  • HNSW index for fast retrieval         │     │   │
│   │  │   ↓ search  ───┼─→│  • Access-controlled (user-scoped)       │     │   │
│   │  │   ↓ context    │  │                                           │     │   │
│   │  │   ↓ LLM        │  └──────────────────────────────────────────┘     │   │
│   │  │   ↓ answer     │                                                    │   │
│   │  └────────────────┘                                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                               │
│                                                                                  │
│   ┌───────────────────────┐  ┌────────────────┐  ┌──────────────────────────┐  │
│   │    PostgreSQL 16      │  │     Redis 7    │  │      Ollama              │  │
│   │    + pgvector         │  │                │  │                          │  │
│   │                       │  │ • Rate limits  │  │ • Llama 3 (chat)         │  │
│   │ • users              │  │ • Cache        │  │ • nomic-embed-text       │  │
│   │ • chat_sessions      │  │ • Sessions     │  │   (embeddings)           │  │
│   │ • chat_messages      │  │                │  │                          │  │
│   │ • documents          │  │                │  │ • Runs locally           │  │
│   │ • document_chunks    │  │                │  │ • No API keys            │  │
│   │   (+ vector index)   │  │                │  │ • No cost                │  │
│   │ • audit_logs         │  │                │  │                          │  │
│   │ • attack_logs        │  │                │  │                          │  │
│   │ • model_configs      │  │                │  │                          │  │
│   │ • roles              │  │                │  │                          │  │
│   └───────────────────────┘  └────────────────┘  └──────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                       INFRASTRUCTURE                                              │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                         Deployment                                        │  │
│   │                                                                          │  │
│   │  LOCAL           KUBERNETES                AWS (TERRAFORM)                │  │
│   │  ─────           ──────────                ───────────────                │  │
│   │  Docker          Kustomize overlays        VPC + Subnets                  │  │
│   │  Compose         HPA (auto-scale)          ECS Fargate                    │  │
│   │                  Ingress + TLS             ALB + Target Groups             │  │
│   │                  Network Policies          RDS PostgreSQL                  │  │
│   │                  StatefulSet (PG)          ECR (container registry)        │  │
│   │                                                                          │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                        Observability                                      │  │
│   │                                                                          │  │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │  │
│   │  │ Prometheus   │  │   Grafana    │  │     Structured Logging       │  │  │
│   │  │              │  │              │  │                              │  │  │
│   │  │ • Metrics    │  │ • Dashboards │  │ • structlog (JSON)           │  │  │
│   │  │ • Alerts     │  │ • Panels     │  │ • Request tracing            │  │  │
│   │  │ • Scraping   │  │ • Viz        │  │ • Security event logging     │  │  │
│   │  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │  │
│   │                                                                          │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                          CI/CD                                            │  │
│   │                                                                          │  │
│   │  GitHub Actions:                                                          │  │
│   │  push → lint → test → security scan → build → deploy staging → deploy prod│  │
│   │                                                                          │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Request Flow (Sequence)

```
User                Frontend            Backend              Security Engine        AI Gateway           Ollama
 │                    │                   │                       │                    │                  │
 │─── Send message ──→│                   │                       │                    │                  │
 │                    │── POST /chat/ ───→│                       │                    │                  │
 │                    │                   │── authenticate ──→ JWT│                    │                  │
 │                    │                   │← user verified ───────│                    │                  │
 │                    │                   │                       │                    │                  │
 │                    │                   │── check rate limit ──→│ Redis              │                  │
 │                    │                   │← allowed ─────────────│                    │                  │
 │                    │                   │                       │                    │                  │
 │                    │                   │── analyze prompt ────→│                    │                  │
 │                    │                   │                       │── injection check  │                  │
 │                    │                   │                       │── jailbreak check  │                  │
 │                    │                   │                       │── PII check        │                  │
 │                    │                   │                       │── heuristic check  │                  │
 │                    │                   │← verdict (allow) ─────│                    │                  │
 │                    │                   │                       │                    │                  │
 │                    │                   │── mask PII if needed ─│                    │                  │
 │                    │                   │                       │                    │                  │
 │                    │                   │── route to model ─────────────────────────→│                  │
 │                    │                   │                       │                    │── generate ─────→│
 │                    │                   │                       │                    │← response ───────│
 │                    │                   │← response ────────────────────────────────│                  │
 │                    │                   │                       │                    │                  │
 │                    │                   │── filter response ───→│                    │                  │
 │                    │                   │                       │── PII in output?   │                  │
 │                    │                   │                       │── prompt leak?     │                  │
 │                    │                   │← filtered response ──│                    │                  │
 │                    │                   │                       │                    │                  │
 │                    │                   │── log to audit_logs ─→│ PostgreSQL         │                  │
 │                    │                   │                       │                    │                  │
 │                    │← JSON response ──│                       │                    │                  │
 │← render message ──│                   │                       │                    │                  │
 │                    │                   │                       │                    │                  │
```

## Attack Blocked Flow

```
Attacker            Frontend            Backend              Security Engine
 │                    │                   │                       │
 │── "Ignore all     │                   │                       │
 │    instructions"──→│                   │                       │
 │                    │── POST /chat/ ───→│                       │
 │                    │                   │── analyze prompt ────→│
 │                    │                   │                       │── INJECTION DETECTED
 │                    │                   │                       │   score: 0.92
 │                    │                   │                       │   action: BLOCK
 │                    │                   │← verdict (block) ─────│
 │                    │                   │                       │
 │                    │                   │── log to attack_logs ─│
 │                    │                   │                       │
 │                    │← 422 BLOCKED ────│                       │
 │← "Request blocked │                   │                       │
 │   by security     │                   │                       │
 │   engine" ────────│                   │                       │
```

## Component Dependency Map

```
┌────────────────────────────────────────────────────────────────┐
│                    SERVICE DEPENDENCIES                          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Frontend ──────→ Backend API                                   │
│                      │                                          │
│                      ├──→ PostgreSQL (data persistence)          │
│                      ├──→ Redis (rate limiting, cache)           │
│                      ├──→ Ollama (AI inference, embeddings)      │
│                      │                                          │
│                      └──→ [Optional] OpenAI / Anthropic / Google │
│                                                                 │
│  Prometheus ────→ Backend /metrics endpoint                      │
│  Grafana ───────→ Prometheus                                    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
SentinelAI/
├── frontend/                          # Next.js 14 React app
│   ├── src/app/                       # App Router pages
│   ├── src/components/                # Reusable UI components
│   ├── src/lib/                       # API client, auth store
│   └── e2e/                           # Playwright E2E tests
│
├── backend/                           # FastAPI Python app
│   ├── app/
│   │   ├── api/v1/endpoints/          # Route handlers
│   │   ├── core/                      # Config, DB, auth, cache
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   ├── schemas/                   # Pydantic request/response
│   │   ├── services/                  # Business logic
│   │   ├── repositories/             # Data access layer
│   │   ├── security/                  # Detection engine
│   │   │   ├── detectors/            # Individual threat detectors
│   │   │   ├── filters/              # Output filters
│   │   │   ├── engine.py             # Orchestrator
│   │   │   └── scoring.py            # Score aggregation
│   │   ├── gateway/                   # AI model routing
│   │   │   ├── providers/            # LLM provider adapters
│   │   │   ├── router.py             # Routing + fallback
│   │   │   └── circuit_breaker.py    # Failure isolation
│   │   ├── guardrails/               # NeMo Guardrails
│   │   ├── rag/                       # RAG pipeline
│   │   └── middleware/               # HTTP middleware
│   ├── alembic/                       # DB migrations
│   └── tests/                         # pytest test suites
│
├── infrastructure/
│   ├── kubernetes/                    # K8s manifests + Kustomize
│   ├── terraform/                     # AWS IaC modules
│   └── monitoring/                    # Prometheus + Grafana
│
├── docs/
│   ├── architecture/                  # This document
│   ├── adr/                           # Architecture decisions
│   ├── api/                           # OpenAPI spec
│   └── runbook.md                     # Operations guide
│
├── docker-compose.yml                 # Local development
├── docker-compose.prod.yml            # Production override
├── Makefile                           # Dev workflow commands
└── .github/workflows/                 # CI/CD pipelines
```

## Technology Decisions

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | Next.js 14 | SSR, App Router, TypeScript, great DX |
| Backend | FastAPI | Async, auto-docs, Pydantic validation, fast |
| Database | PostgreSQL + pgvector | Proven, vector search built-in, no extra service |
| Cache | Redis | Industry standard, rate limiting support |
| AI (free) | Ollama | Local inference, no cost, privacy |
| AI (paid) | OpenAI/Anthropic/Google | Best quality when budget allows |
| Container | Docker | Standard, portable |
| Orchestration | Kubernetes | Production scaling, self-healing |
| IaC | Terraform | Multi-cloud, declarative, state management |
| CI/CD | GitHub Actions | Integrated, free for open source |
| Monitoring | Prometheus + Grafana | Open source, battle-tested |

★ = Default (free) option
