# ADR-005: Kubernetes Deployment with Kustomize Overlays

## Status: Accepted

## Context

SentinelAI needs a deployment strategy that supports:

- Multiple environments (development, staging, production)
- Horizontal scaling for the API layer under variable load
- Stateful workloads (PostgreSQL, Redis) with proper lifecycle management
- Rolling updates with zero-downtime deployments
- Resource isolation between components
- Infrastructure as code with environment-specific configuration

## Decision

We deploy SentinelAI on **Kubernetes** using **Kustomize overlays** for environment management, with HPA for autoscaling and StatefulSets for databases.

### Architecture

```
├── infrastructure/k8s/
│   ├── base/                    # Shared manifests
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── redis-statefulset.yaml
│   │   └── kustomization.yaml
│   ├── overlays/
│   │   ├── development/         # Local/dev settings
│   │   ├── staging/             # Pre-production
│   │   └── production/          # Production overrides
│   └── components/
│       ├── monitoring/          # Prometheus + Grafana
│       └── ingress/             # NGINX Ingress
```

### Key design choices:

1. **Kustomize over Helm** — Simpler mental model, no template language, native kubectl support. Environment differences are expressed as patches, not conditionals.

2. **HPA (Horizontal Pod Autoscaler)** for stateless services:
   - Backend API: Scale 2–10 pods based on CPU (70%) and custom metrics (request latency)
   - Frontend: Scale 2–5 pods based on CPU

3. **StatefulSet for databases:**
   - PostgreSQL: StatefulSet with persistent volume claims, scheduled backups to S3
   - Redis: StatefulSet with AOF persistence, Sentinel for failover in production

4. **Resource limits on all pods:**
   - Backend: 256Mi–1Gi memory, 250m–1000m CPU
   - Frontend: 128Mi–512Mi memory, 100m–500m CPU
   - PostgreSQL: 512Mi–2Gi memory, 500m–2000m CPU

5. **Rolling update strategy:**
   - maxSurge: 1, maxUnavailable: 0 (zero-downtime)
   - Readiness probes gate traffic routing
   - PodDisruptionBudgets ensure minimum availability

6. **Network policies:**
   - Backend can reach PostgreSQL and Redis
   - Frontend can only reach Backend
   - No direct external access to databases

## Consequences

**Positive:**
- Consistent deployment across all environments
- Auto-scaling handles traffic spikes without manual intervention
- StatefulSets provide proper data persistence guarantees
- Kustomize patches keep environment differences minimal and auditable
- Network policies enforce least-privilege communication
- Infrastructure as code enables GitOps workflows

**Negative:**
- Kubernetes adds operational complexity (requires team expertise)
- StatefulSets are more complex to manage than managed database services
- Local development requires minikube/kind setup or Docker Compose fallback
- Resource limits require careful tuning to avoid OOM kills
- Monitoring and alerting infrastructure must be maintained

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **AWS ECS/Fargate** | Vendor lock-in to AWS; less portable; weaker ecosystem for stateful workloads |
| **Docker Compose in production** | No auto-scaling, no self-healing, no rolling updates, single-host limitation |
| **Helm charts** | Template complexity; harder to diff between environments; Kustomize is simpler for our needs |
| **Serverless (Lambda/Cloud Run)** | Cold starts unacceptable for real-time chat; connection pooling issues with PostgreSQL; not suitable for WebSocket streaming |
| **Managed Kubernetes (EKS/GKE)** | Actually compatible — we use Kustomize overlays that work on any K8s. Cloud-managed control plane is recommended for production |
