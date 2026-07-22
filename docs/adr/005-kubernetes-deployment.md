# ADR-005: Kubernetes with Kustomize overlays

**Status:** Accepted

**Context:** Need deployment that works for local dev (Docker Compose), staging, and production. Want to avoid duplicating config across environments.

**Decision:** Kustomize overlays on a base set of K8s manifests.

- `base/` has the canonical resource definitions
- `overlays/dev/` patches replicas=1, lower resource limits
- `overlays/prod/` patches replicas=3, higher limits, prod env vars
- HPA on backend (2-10 pods, 70% CPU target)
- StatefulSet for PostgreSQL (persistent volume)
- Ingress with TLS for external access

**Why not Helm?**
- Kustomize is built into kubectl (no extra tooling)
- Our config isn't complex enough to need templating — patches are sufficient
- Easier to read (plain YAML vs Go templates)

**Tradeoffs:**
- Less flexible than Helm for highly parameterized deployments
- No release management (solved by CI/CD pipeline tracking image tags)
- StatefulSet for DB is fine for dev/staging but prod should use managed RDS

**Rejected:**
- Helm — overkill for this project, harder to debug templates
- Docker Compose in prod — no auto-scaling, no self-healing, no rolling updates
- AWS-only (ECS) — locks us into one cloud
