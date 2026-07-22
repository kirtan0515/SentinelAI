# SentinelAI - Enterprise AI Security Gateway

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-14-black.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## Overview

SentinelAI is a cloud-native AI security platform that sits between enterprise users and Large Language Models (OpenAI, Anthropic Claude, Google Gemini, Ollama/Llama). It protects LLM applications from prompt injection, jailbreak attacks, data leakage, unauthorized access, and insecure AI usage while providing monitoring, authentication, auditing, and secure Retrieval-Augmented Generation (RAG).

## Architecture

```
User → Frontend (Next.js) → API Gateway → Authentication → Security Engine → Guardrails → Model Router → LLM
                                                                                                          ↓
User ← Frontend ← Response Filter ← Audit Logging ← ─────────────────────────────────────────── Response
```

## Core Features

- **AI Security Gateway** - Every AI request passes through security checks before reaching LLMs
- **Prompt Injection Detection** - Detects and blocks malicious prompt injection attempts
- **Jailbreak Detection** - Identifies and rejects common jailbreak attack patterns
- **Sensitive Data Detection** - Masks credit cards, SSNs, API keys, passwords before they reach models
- **Secure RAG** - Upload documents, generate embeddings, query with pgvector
- **Multi-Model Router** - Supports GPT, Claude, Gemini, Llama (Ollama)
- **NVIDIA NeMo Guardrails** - Input/output guardrails for model interactions
- **RBAC & Authentication** - AWS Cognito, OAuth2, JWT, MFA
- **Audit Logging** - Complete request tracking with attack detection
- **Monitoring Dashboard** - Real-time metrics, blocked attacks, system health
- **Admin Portal** - User management, model configuration, guardrail settings

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL 15, pgvector |
| Auth | AWS Cognito, OAuth2, JWT, RBAC, MFA |
| AI | OpenAI API, Anthropic Claude, Google Gemini, Ollama/Llama |
| Guardrails | NVIDIA NeMo Guardrails |
| Infrastructure | Docker, Docker Compose, Kubernetes, Terraform |
| Cloud | AWS (ECS, RDS, S3, CloudWatch) |
| Monitoring | Prometheus, Grafana, CloudWatch |
| CI/CD | GitHub Actions |

## Project Structure

```
SentinelAI/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # Reusable React components
│   │   ├── lib/             # Utilities and API client
│   │   ├── hooks/           # Custom React hooks
│   │   └── types/           # TypeScript type definitions
│   └── ...
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── api/             # API route handlers
│   │   ├── core/            # Configuration and dependencies
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic layer
│   │   ├── repositories/    # Data access layer
│   │   ├── security/        # Security engine (injection, jailbreak, PII)
│   │   ├── guardrails/      # NVIDIA NeMo Guardrails
│   │   ├── rag/             # RAG pipeline
│   │   └── middleware/      # Custom middleware
│   ├── alembic/             # Database migrations
│   └── tests/               # Test suites
├── infrastructure/           # DevOps and deployment
│   ├── docker/              # Dockerfiles
│   ├── kubernetes/          # K8s manifests
│   ├── terraform/           # Infrastructure as Code
│   └── monitoring/          # Prometheus & Grafana configs
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── .github/workflows/        # CI/CD pipelines
├── docker-compose.yml        # Local development orchestration
└── .env.example              # Environment variable template
```

## Quick Start
## Quick Start (100% Free)

### Prerequisites

- Docker Desktop ([download](https://docker.com/products/docker-desktop))
- Ollama ([download](https://ollama.com/download))
- Node.js 18+ ([download](https://nodejs.org))
- Python 3.11+

### Setup (5 minutes)

```bash
# 1. Clone
git clone https://github.com/kirtan0515/SentinelAI.git
cd SentinelAI

# 2. Start database + cache
docker-compose up -d postgres redis

# 3. Pull free AI models (runs locally, no API key needed)
ollama pull llama3
ollama pull nomic-embed-text

# 4. Start Ollama (keep this running)
ollama serve

# 5. Backend setup (new terminal)
cd backend
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Open

- **Website:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- Register an account, login, and start chatting

### Cost

| Component | Cost |
|-----------|------|
| SentinelAI | Free (MIT) |
| PostgreSQL + Redis | Free (Docker) |
| Ollama + Llama 3 | Free (local) |
| RAG embeddings | Free (nomic-embed-text via Ollama) |
| GPT-4, Claude (optional) | Paid API keys |

Everything works without any API keys. Cloud AI models are optional.

### Development Setup

See [Developer Guide](docs/developer-guide.md) for detailed setup instructions.

## Development Milestones

### Phase 1: Foundation
- [x] Project structure and scaffolding
- [x] Docker Compose setup
- [x] Database schema design
- [x] Basic authentication (JWT)
- [x] CI/CD pipeline

### Phase 2: Core Security Engine
- [ ] Prompt injection detection
- [ ] Jailbreak detection
- [ ] Sensitive data masking
- [ ] Security scoring

### Phase 3: AI Gateway
- [ ] Multi-model router (GPT, Claude, Gemini, Llama)
- [ ] Request/response pipeline
- [ ] Rate limiting and throttling
- [ ] NVIDIA NeMo Guardrails

### Phase 4: RAG System
- [ ] Document upload and processing
- [ ] Embedding generation
- [ ] pgvector storage and retrieval
- [ ] Access-controlled document queries

### Phase 5: Frontend & Dashboards
- [ ] Authentication UI
- [ ] AI Chat interface
- [ ] Security analytics dashboard
- [ ] Admin portal
- [ ] Monitoring dashboard

### Phase 6: Production Readiness
- [ ] Kubernetes deployment
- [ ] Terraform infrastructure
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Security hardening

## Security

This project follows the [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/) guidelines.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
