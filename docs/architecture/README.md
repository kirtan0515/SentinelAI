# SentinelAI Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
│                    Next.js + React + TypeScript                       │
│                    Tailwind CSS + shadcn/ui                           │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                                   │
│                     FastAPI + Uvicorn                                 │
│  ┌──────────┐  ┌───────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   Auth   │  │ Rate Limiter  │  │   CORS   │  │   Logging    │  │
│  └──────────┘  └───────────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SECURITY ENGINE                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Prompt Injection  │  │ Jailbreak Detect │  │  PII Detection   │  │
│  │    Detection      │  │                  │  │  & Masking       │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     NVIDIA NeMo GUARDRAILS                            │
│              Input Guardrails │ Output Guardrails                     │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MODEL ROUTER                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  OpenAI  │  │ Anthropic│  │  Google   │  │  Ollama (Local)  │  │
│  │  GPT-4   │  │  Claude  │  │  Gemini   │  │     Llama 2      │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  PostgreSQL   │  │    Redis     │  │       pgvector           │  │
│  │  (Primary DB) │  │  (Cache/RL)  │  │  (Vector Embeddings)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow

1. **User** sends request from frontend
2. **API Gateway** receives and authenticates request (JWT/Cognito)
3. **Security Engine** analyzes prompt for threats
4. **Guardrails** apply additional safety checks
5. **Model Router** sends to appropriate LLM provider
6. **Response Filter** checks LLM output
7. **Audit Logger** records complete interaction
8. **Response** returned to user

## Key Design Decisions

- **Clean Architecture**: Separation of concerns with service/repository pattern
- **Async-first**: All I/O operations use async/await
- **Defense in Depth**: Multiple security layers (auth, engine, guardrails)
- **Provider Agnostic**: Model router abstracts LLM providers
- **Observability**: Prometheus metrics + structured logging
- **Zero Trust**: Every request authenticated and analyzed
