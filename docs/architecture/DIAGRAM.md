# SentinelAI Architecture Diagram

## System Overview

```mermaid
graph TB
    subgraph Clients
        Browser[🌐 Browser]
        API[🔌 API Client]
    end

    subgraph Frontend["Frontend (Next.js 14)"]
        Landing[Landing Page]
        Auth[Login / Register]
        Dashboard[Dashboard + Charts]
        Chat[AI Chat + RAG]
        Admin[Admin Portal]
    end

    subgraph LoadBalancer["Load Balancer"]
        ALB[Application Load Balancer<br/>TLS Termination]
    end

    subgraph Backend["Backend API (FastAPI)"]
        direction TB
        MW[Middleware Stack<br/>CORS • Security Headers • Rate Limiter]
        Routes[API Routes<br/>/auth /chat /documents /security /admin /audit /models]
        DI[Dependency Injection<br/>DB Sessions • JWT Auth • RBAC]
    end

    subgraph SecurityEngine["Security Engine"]
        direction TB
        Injection[🛡️ Prompt Injection<br/>Detector<br/>40+ patterns]
        Jailbreak[🔒 Jailbreak<br/>Detector<br/>50+ patterns]
        PII[👁️ Sensitive Data<br/>Detector + Masker]
        Heuristic[📊 Heuristic<br/>Analyzer]
        Scorer[Security Scorer<br/>allow / flag / mask / block]
    end

    subgraph Gateway["AI Gateway"]
        Router[Gateway Router]
        CB[Circuit Breaker]
        Retry[Retry + Fallback]
    end

    subgraph LLMs["LLM Providers"]
        Ollama[🟢 Ollama<br/>Llama 3<br/>FREE ★]
        OpenAI[OpenAI<br/>GPT-4<br/>paid]
        Anthropic[Anthropic<br/>Claude<br/>paid]
        Google[Google<br/>Gemini<br/>paid]
    end

    subgraph RAG["RAG Pipeline"]
        Extract[Extract Text<br/>PDF / DOCX / TXT]
        Chunk[Chunk<br/>Recursive + Overlap]
        Embed[Embed<br/>Ollama nomic-embed ★<br/>FREE]
        Search[Vector Search<br/>Cosine Similarity]
    end

    subgraph DataLayer["Data Layer"]
        PG[(PostgreSQL 16<br/>+ pgvector)]
        Redis[(Redis 7<br/>Cache + Rate Limits)]
        OllamaLocal[Ollama Server<br/>Local Inference]
    end

    subgraph Monitoring["Observability"]
        Prometheus[Prometheus<br/>Metrics + Alerts]
        Grafana[Grafana<br/>Dashboards]
        Logs[Structured Logging<br/>structlog JSON]
    end

    subgraph CICD["CI/CD"]
        GHA[GitHub Actions<br/>Lint → Test → Build → Deploy]
    end

    subgraph Deployment["Deployment Options"]
        Docker[🐳 Docker Compose<br/>Local Dev]
        K8s[☸️ Kubernetes<br/>Kustomize + HPA]
        AWS[☁️ AWS<br/>ECS + RDS + ALB]
    end

    %% Connections
    Clients --> ALB
    ALB --> Frontend
    Frontend -->|REST + WebSocket| Backend
    Backend --> SecurityEngine
    SecurityEngine --> Gateway
    Gateway --> LLMs
    Backend -->|Documents| RAG
    RAG --> PG
    Gateway --> OllamaLocal
    Backend --> PG
    Backend --> Redis
    Embed --> OllamaLocal
    Prometheus --> Backend
    Grafana --> Prometheus

    %% Styling
    classDef free fill:#22c55e,stroke:#16a34a,color:#fff
    classDef paid fill:#6b7280,stroke:#4b5563,color:#fff
    classDef security fill:#ef4444,stroke:#dc2626,color:#fff
    classDef gateway fill:#8b5cf6,stroke:#7c3aed,color:#fff

    class Ollama,OllamaLocal,Embed free
    class OpenAI,Anthropic,Google paid
    class Injection,Jailbreak,PII,Heuristic,Scorer security
    class Router,CB,Retry gateway
```

## Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant S as Security Engine
    participant G as AI Gateway
    participant O as Ollama (FREE)
    participant DB as PostgreSQL

    U->>F: Send message
    F->>B: POST /api/v1/chat/
    B->>B: Authenticate (JWT)
    B->>B: Rate limit check (Redis)
    B->>S: Analyze prompt
    
    alt Threat Detected
        S-->>B: BLOCK (score > 0.7)
        B-->>F: 422 "Blocked by security"
        B->>DB: Log to attack_logs
        F-->>U: ⚠️ Request blocked
    else Safe
        S-->>B: ALLOW (score < 0.7)
        B->>B: Mask PII if detected
        B->>G: Route to model
        G->>O: Generate response
        O-->>G: AI response
        G-->>B: Response + metadata
        B->>S: Filter output (PII, leaks)
        B->>DB: Log to audit_logs
        B-->>F: JSON response
        F-->>U: Display message + security badge
    end
```

## Data Model

```mermaid
erDiagram
    USERS ||--o{ CHAT_SESSIONS : has
    USERS ||--o{ DOCUMENTS : uploads
    USERS }|--|| ROLES : belongs_to
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : contains
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : split_into
    
    USERS {
        uuid id PK
        string email UK
        string username UK
        string hashed_password
        string role
        boolean is_active
        boolean mfa_enabled
        timestamp last_login
    }
    
    CHAT_SESSIONS {
        uuid id PK
        uuid user_id FK
        string title
        string model
        timestamp created_at
    }
    
    CHAT_MESSAGES {
        uuid id PK
        uuid session_id FK
        string role
        text content
        float security_score
        boolean blocked
    }
    
    DOCUMENTS {
        uuid id PK
        uuid user_id FK
        string filename
        string status
        int chunk_count
    }
    
    DOCUMENT_CHUNKS {
        uuid id PK
        uuid document_id FK
        text content
        int chunk_index
        vector embedding
    }
    
    AUDIT_LOGS {
        uuid id PK
        uuid user_id
        string endpoint
        text prompt
        float security_score
        boolean attack_detected
        boolean blocked
    }
    
    ATTACK_LOGS {
        uuid id PK
        uuid user_id
        string attack_type
        string severity
        float confidence
        text original_prompt
        string action_taken
    }
    
    MODEL_CONFIGS {
        uuid id PK
        string provider
        string model_name
        boolean is_default
        boolean is_enabled
        float cost_per_1k_input
    }
```

## Deployment Architecture (AWS)

```mermaid
graph TB
    subgraph VPC["AWS VPC"]
        subgraph Public["Public Subnets"]
            ALB[Application Load Balancer]
            NAT[NAT Gateway]
        end
        
        subgraph Private["Private Subnets"]
            subgraph ECS["ECS Fargate Cluster"]
                BE1[Backend Task 1]
                BE2[Backend Task 2]
                BE3[Backend Task 3]
                FE1[Frontend Task 1]
                FE2[Frontend Task 2]
            end
            
            RDS[(RDS PostgreSQL<br/>Multi-AZ + pgvector)]
            ElastiCache[(ElastiCache Redis)]
        end
    end
    
    Internet[Internet] --> ALB
    ALB --> FE1
    ALB --> FE2
    ALB --> BE1
    ALB --> BE2
    ALB --> BE3
    BE1 --> RDS
    BE2 --> RDS
    BE3 --> RDS
    BE1 --> ElastiCache
    
    subgraph External
        ECR[ECR<br/>Container Registry]
        CW[CloudWatch<br/>Logs + Metrics]
        S3[S3<br/>Terraform State]
    end
    
    ECS --> ECR
    ECS --> CW
```

---

## How to View

1. **On GitHub** — These Mermaid diagrams render automatically when you view this file on github.com
2. **draw.io** — Open `sentinelai-architecture.drawio` at [app.diagrams.net](https://app.diagrams.net) for the full visual diagram with AWS icons
3. **Export** — From draw.io, export as PNG/SVG/PDF for presentations
