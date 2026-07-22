# SentinelAI

A security gateway for LLM applications. Sits between users and AI models (GPT-4, Claude, Gemini, Llama) to detect prompt injection, block jailbreaks, mask sensitive data, and log everything.

Built because I wanted to understand how enterprise AI security actually works at the system level — not just "add a regex filter" but a proper multi-layer detection pipeline with scoring, fallbacks, and audit trails.

## What it does

```
User → Auth → Rate Limit → Security Engine → Guardrails → AI Model → Response Filter → Audit Log → User
```

- Analyzes every prompt for injection/jailbreak patterns (90+ regex categories + heuristic scoring)
- Masks PII (credit cards, SSN, API keys, etc.) before they hit the model
- Routes to multiple LLM providers with circuit breaker + automatic fallback
- Stores document embeddings in pgvector for RAG queries
- Logs every request with security scores for compliance

## Quick start (free, no API keys needed)

Requires: Docker, [Ollama](https://ollama.com/download), Node.js 18+, Python 3.11+

```bash
git clone https://github.com/kirtan0515/SentinelAI.git
cd SentinelAI

# Database + cache
docker-compose up -d postgres redis

# Local AI (free)
ollama pull llama3
ollama pull nomic-embed-text
ollama serve

# Backend (new terminal)
cd backend
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
uvicorn app.main:app --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Register, login, chat. The security engine runs on every message — try typing "ignore previous instructions" and watch it get blocked.

## Tech

**Backend:** FastAPI, SQLAlchemy (async), Pydantic, PostgreSQL + pgvector, Redis

**Frontend:** Next.js 14, TypeScript, Tailwind, Recharts, Zustand

**AI:** Ollama (Llama 3 for chat, nomic-embed-text for RAG). Optionally supports OpenAI/Anthropic/Google if you add API keys.

**Infra:** Docker Compose (local), Kubernetes manifests + Terraform modules (prod), GitHub Actions CI/CD

## Project structure

```
backend/
  app/
    security/        # Detection engine (injection, jailbreak, PII, heuristics)
    gateway/         # Multi-model router with circuit breaker
    rag/             # Document processing + vector search pipeline
    api/v1/          # REST endpoints + WebSocket streaming
    middleware/      # Rate limiting, security headers
frontend/
  src/app/           # Next.js pages (dashboard, chat, admin, etc.)
infrastructure/
  kubernetes/        # K8s manifests with Kustomize overlays
  terraform/         # AWS modules (VPC, ECS, RDS)
  monitoring/        # Prometheus + Grafana
```

## Architecture

See [docs/architecture/DIAGRAM.md](docs/architecture/DIAGRAM.md) for full diagrams (renders on GitHub).

## Status

Working locally with Docker + Ollama. Security engine is the most complete part — the detection pipeline, scoring system, and response filter are fully implemented and tested. Dashboard shows mock data for now (wiring up real-time stats from audit logs is next).

## License

MIT
