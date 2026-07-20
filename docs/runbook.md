# SentinelAI On-Call Runbook

## Service Architecture Overview

| Service | Port | Description | Dependencies |
|---------|------|-------------|--------------|
| Backend API | 8000 | FastAPI application server | PostgreSQL, Redis, AI Providers |
| Frontend | 3000 | Next.js web application | Backend API |
| PostgreSQL | 5432 | Primary database + pgvector | Persistent volume |
| Redis | 6379 | Cache, rate limiting, sessions | — |
| Ollama | 11434 | Local LLM inference | GPU (optional) |
| Prometheus | 9090 | Metrics collection | All services |
| Grafana | 3001 | Metrics visualization | Prometheus |

### Service Communication Flow

```
User → Frontend (3000) → Backend API (8000) → AI Providers (external)
                                ↓
                         PostgreSQL (5432)
                         Redis (6379)
```

---

## Common Alerts and Response

### High API Latency (>2s p95)

**Symptoms:** Slow chat responses, timeout errors in frontend.

**Investigation:**
1. Check AI provider status pages (OpenAI, Anthropic, Google)
2. Check circuit breaker state: `GET /api/v1/gateway/health`
3. Check database connection pool: monitor `pg_stat_activity`
4. Check Redis connectivity: `redis-cli ping`

**Resolution:**
- If provider degraded → circuit breaker should auto-failover; verify fallback is active
- If DB connections exhausted → restart backend pods; check for long-running queries
- If Redis down → restart Redis; backend will operate without cache (degraded)

### Circuit Breaker Open

**Symptoms:** Requests to specific AI provider failing immediately.

**Investigation:**
1. Check provider status page
2. Review logs: `docker-compose logs backend | grep "circuit_breaker"`
3. Check Grafana dashboard: "AI Gateway" panel

**Resolution:**
- Wait for half-open state (60s timeout) and automatic recovery
- If provider confirmed down, no action needed — fallback is handling traffic
- To force reset: restart backend service (circuit breaker state resets)

### Database Connection Errors

**Symptoms:** 500 errors across all endpoints, "connection refused" in logs.

**Investigation:**
1. Check PostgreSQL status: `docker-compose ps postgres`
2. Check disk space: `docker exec sentinelai-postgres df -h`
3. Check connections: `SELECT count(*) FROM pg_stat_activity;`
4. Check PostgreSQL logs: `docker-compose logs postgres`

**Resolution:**
- If OOM killed → increase memory limits; restart: `docker-compose restart postgres`
- If disk full → expand volume; clean old audit logs
- If too many connections → restart backend pods to release pool

### Rate Limit Spikes

**Symptoms:** Many 429 responses, specific users or IPs hitting limits.

**Investigation:**
1. Check Redis rate limit keys: `redis-cli keys "rate_limit:*"`
2. Review audit logs for the IP/user
3. Check if legitimate traffic spike or attack

**Resolution:**
- Legitimate spike → temporarily increase limits in config
- Attack → add IP to blocklist; review security logs
- Bug → check if rate limit reset is functioning

### Security Events Spike

**Symptoms:** High volume of blocked requests, attack_logs table growing rapidly.

**Investigation:**
1. Query recent attacks: `SELECT attack_type, count(*) FROM attack_logs WHERE created_at > now() - interval '1 hour' GROUP BY attack_type;`
2. Check if single source or distributed
3. Review specific blocked prompts for false positives

**Resolution:**
- Single source → block IP at infrastructure level (WAF/security group)
- Distributed → enable enhanced rate limiting; consider CAPTCHA
- False positives → adjust detector thresholds in `guardrails/config/config.yml`

---

## Rollback Procedures

### Docker Compose Rollback

```bash
# Stop current version
docker-compose down

# Checkout previous version
git checkout <previous-tag>

# Rebuild and start
docker-compose build
docker-compose up -d
```

### Kubernetes Rollback

```bash
# Check rollout history
kubectl rollout history deployment/sentinelai-backend -n sentinelai

# Rollback to previous revision
kubectl rollout undo deployment/sentinelai-backend -n sentinelai

# Rollback to specific revision
kubectl rollout undo deployment/sentinelai-backend -n sentinelai --to-revision=3

# Verify rollback
kubectl rollout status deployment/sentinelai-backend -n sentinelai
```

### Database Rollback

```bash
# Check current migration
cd backend && alembic current

# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# WARNING: Data loss may occur on downgrade. Always backup first.
```

---

## Health Check Endpoints

| Endpoint | Expected Response | Purpose |
|----------|-------------------|---------|
| `GET /health` | `{"status": "healthy"}` | Basic liveness |
| `GET /api/v1/gateway/health` | Provider status + circuit breaker state | AI gateway health |
| `GET /docs` | Swagger UI loads | API documentation available |

**Automated health check:**
```bash
curl -sf http://localhost:8000/health | jq .status
```

---

## Log Locations

### Docker Compose

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Structured Logging (Backend)

Backend uses `structlog` with JSON output. Key fields:
- `event` — Log message
- `level` — info/warning/error
- `user_id` — Associated user (if authenticated)
- `request_id` — Correlation ID for request tracing
- `latency_ms` — Request duration

### CloudWatch (Production)

```bash
# View log group
aws logs tail /ecs/sentinelai-backend --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /ecs/sentinelai-backend \
  --filter-pattern "ERROR"
```

---

## Scaling Procedures

### Manual Scaling (Docker Compose)

```bash
# Scale backend to 3 instances (requires load balancer)
docker-compose up -d --scale backend=3
```

### Manual Scaling (Kubernetes)

```bash
# Scale deployment
kubectl scale deployment sentinelai-backend -n sentinelai --replicas=5

# Check HPA status
kubectl get hpa -n sentinelai
```

### Auto-Scaling Configuration (HPA)

```yaml
# Current HPA settings
minReplicas: 2
maxReplicas: 10
metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
```

**When to manually scale:**
- Anticipated traffic spike (product launch, demo)
- HPA not scaling fast enough for sudden load
- After scaling, monitor for 10 minutes then verify HPA resumes control

---

## Database Operations

### Backup

```bash
# Full backup
docker exec sentinelai-postgres pg_dump -U sentinelai sentinelai > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup specific tables
docker exec sentinelai-postgres pg_dump -U sentinelai -t audit_logs -t attack_logs sentinelai > security_backup.sql

# Compressed backup
docker exec sentinelai-postgres pg_dump -U sentinelai sentinelai | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Restore from backup (WARNING: destructive)
docker exec -i sentinelai-postgres psql -U sentinelai sentinelai < backup.sql

# Restore to a new database first (safer)
docker exec sentinelai-postgres createdb -U sentinelai sentinelai_restore
docker exec -i sentinelai-postgres psql -U sentinelai sentinelai_restore < backup.sql
```

### Migrations

```bash
# Check current state
cd backend && alembic current

# Run pending migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "description"

# IMPORTANT: Always backup before running migrations in production
```

### Common Database Queries

```sql
-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;

-- Active connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- Long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC;

-- Kill a stuck query
SELECT pg_terminate_backend(<pid>);
```

---

## Security Incident Response

### Credential Leak

**Severity: Critical**

1. **Immediately rotate** the leaked credential:
   - API keys: Regenerate in provider dashboard
   - JWT secret: Update `JWT_SECRET_KEY` and redeploy (invalidates all sessions)
   - Database password: Update in PostgreSQL and all connection strings
2. Review audit logs for unauthorized access during exposure window
3. Notify affected users if data access is confirmed
4. Post-mortem: identify how the leak occurred, add prevention controls

### Attack Spike (Sustained)

**Severity: High**

1. Identify attack source(s) from `attack_logs`:
   ```sql
   SELECT ip_address, count(*), array_agg(DISTINCT attack_type)
   FROM attack_logs WHERE created_at > now() - interval '1 hour'
   GROUP BY ip_address ORDER BY count DESC LIMIT 20;
   ```
2. Block top offending IPs at infrastructure level (WAF/security group)
3. Temporarily tighten rate limits
4. Monitor for continued attempts from new IPs (distributed attack)
5. If attack is overwhelming, enable maintenance mode

### Data Breach

**Severity: Critical**

1. **Contain:** Isolate affected systems. Take backend offline if necessary.
2. **Assess:** Determine scope — what data was accessed, how many users affected
3. **Notify:** Legal team, management, affected users (per regulatory requirements)
4. **Remediate:** Patch the vulnerability, rotate all credentials
5. **Document:** Full timeline for regulatory compliance (GDPR 72-hour notification)

---

## Contact Information

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call Engineer | [PagerDuty rotation] | — |
| Backend Lead | [TBD] | After 30min unresolved |
| Security Lead | [TBD] | Any security incident |
| Infrastructure | [TBD] | Database/K8s issues |
| Management | [TBD] | Critical incidents only |

**Escalation Policy:**
- P1 (service down): Page immediately, 15-min response SLA
- P2 (degraded): Page during business hours, 1-hour response SLA
- P3 (non-urgent): Slack notification, next business day
