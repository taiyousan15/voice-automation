# ADR-004: Deployment Platform Selection (VPS + Optional Cloud)

**Status**: Accepted

**Date**: 2026-02-11

**Decision Makers**: Architecture Committee

---

## Context

The podcast system requires reliable hosting for daily scheduled tasks (3+ episodes/day). Key constraints:

- **Availability**: 99.0% uptime SLA (REQ-901)
- **Latency**: Episode processing within 24 hours
- **Cost**: ¥3,000-8,000/month infrastructure (within budget)
- **Scalability**: Support 3 themes initially, scale to 10+ themes
- **Operational Complexity**: Minimize DevOps overhead
- **Data Persistence**: PostgreSQL database, file storage for audio

---

## Decision

Adopt a **VPS-centric approach with cloud optionality**:

```
Primary: DigitalOcean Droplet (¥8,000/month)
  - 4GB RAM, 2 vCPU, 80GB SSD
  - Simple deployment (Docker Compose)
  - Good for initial 3-5 themes

Optional Scaling Path:
  → AWS/GCP for horizontal scaling (10+ themes)
  → Separate container per theme (Kubernetes ready)
```

### Technical Architecture

**Phase 1 (Startup): Single VPS**
```
┌─────────────────────────────────────┐
│ DigitalOcean Droplet (Ubuntu 22.04) │
├─────────────────────────────────────┤
│ - Docker Engine                     │
│ - Docker Compose                    │
│ - PostgreSQL 15                     │
│ - Redis (caching)                   │
│ - Prometheus (monitoring)           │
│ - Grafana (dashboards)              │
├─────────────────────────────────────┤
│ Services:                           │
│ - Orchestrator (APScheduler)        │
│ - Data Collector                    │
│ - Script Generator                  │
│ - TTS Engine (Ollama + ElevenLabs) │
│ - Distributor                       │
│ - API Server (FastAPI)              │
└─────────────────────────────────────┘
```

**Phase 2 (Growth): Multi-VPS or Cloud**
```
Option A: Multiple VPS (per theme)
  - Theme 1 Droplet (¥8,000)
  - Theme 2 Droplet (¥8,000)
  - Theme 3 Droplet (¥8,000)
  - Shared PostgreSQL (¥5,000)
  = ¥29,000/month for 3 themes

Option B: Kubernetes (AWS/GCP)
  - EKS or GKE cluster
  - Auto-scaling pods per theme
  - Managed PostgreSQL (RDS/Cloud SQL)
  = ¥25,000-35,000/month for 10+ themes
```

### Deployment Configuration

```yaml
# docker-compose.yml for VPS deployment
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  orchestrator:
    build: ./services/orchestrator
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/podcast
      REDIS_URL: redis://redis:6379

  data_collector:
    build: ./services/data_collector
    depends_on:
      - redis
    environment:
      REDIS_URL: redis://redis:6379

  script_generator:
    build: ./services/script_generator
    depends_on:
      - postgres

  tts_engine:
    build: ./services/tts_engine
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

volumes:
  postgres_data:
```

---

## Consequences

### Benefits ✅

1. **Cost Efficiency**
   - VPS: ¥8,000/month (single droplet for 3-5 themes)
   - Much cheaper than always-on Kubernetes (¥25k+)
   - Pay-as-you-grow model
   - No long-term lock-in

2. **Operational Simplicity**
   - Docker Compose easy to understand
   - Single SSH connection for management
   - Simple backup/restore procedures
   - Minimal DevOps expertise required

3. **Sufficient Performance**
   - 4GB RAM, 2 vCPU adequate for 3-5 concurrent episodes
   - SSD provides good I/O for database
   - CPU headroom for peak load
   - Memory sufficient for Ollama 8B model

4. **Scalability Path**
   - Can add more VPS for horizontal scaling
   - Kubernetes-ready architecture (no major refactoring)
   - Database can be externalized (managed PostgreSQL)
   - Gradual scaling without rearchitecting

5. **Reliability**
   - DigitalOcean 99.9% SLA
   - Managed backups available
   - Geographic redundancy possible
   - Simple disaster recovery (copy droplet)

### Drawbacks ⚠️

1. **Manual Scaling**
   - Horizontal scaling requires manual VPS provisioning
   - No auto-scaling for traffic spikes
   - Requires SSH for deployments

2. **Resource Limitations**
   - Single VPS has capacity ceiling (~5 themes)
   - GPU limitation (single GPU per droplet)
   - Network throughput bottleneck

3. **Operational Overhead**
   - OS patching responsibility (no managed service)
   - Database backups manual (unless paid service)
   - Security updates needed regularly
   - Monitoring setup manual

4. **Latency & Geography**
   - Single data center location (network latency for distant users)
   - No geographic distribution for resilience
   - Limited to one cloud provider region

---

## Alternatives Considered

### ❌ Alternative 1: Kubernetes on Day 1 (EKS/GKE)

**Pros**: Auto-scaling, high availability, industry standard
**Cons**: ¥25k+/month, overkill for startup, steep learning curve, complex operations
**Why Rejected**: Over-engineered for current scale (3 themes). Cost 3x higher than needed. Complexity not justified.

### ❌ Alternative 2: Serverless (AWS Lambda + SQS)

**Pros**: No infrastructure management, pay-per-invocation, scales automatically
**Cons**: Cold start latency (1-2 min), not ideal for long-running tasks, vendor lock-in, hidden costs from long episodes
**Why Rejected**: Script generation/TTS takes 5-30 min (exceeds Lambda 15-min limit for standard). Episodic workload doesn't match Lambda economics.

### ❌ Alternative 3: Managed Container Service (AWS Fargate/Cloud Run)

**Pros**: Managed containers, auto-scaling, no infrastructure
**Cons**: ¥20k+/month for adequate capacity, slightly more complex than VPS
**Why Rejected**: Cost comparable to Kubernetes but less flexible. VPS simpler and cheaper for initial phase.

### ❌ Alternative 4: Self-Managed Kubernetes (on VPS)

**Pros**: Full control, industry standard, can migrate to managed K8s later
**Cons**: K8s on single VPS inefficient, high operational burden, false economy, more complex deployment
**Why Rejected**: K8s overkill for single machine. Better to use Docker Compose now, K8s when multi-node.

---

## Implementation Plan

### Phase 1: VPS Setup (Week 1-2)
- [ ] Provision DigitalOcean Droplet (4GB, 2vCPU, Ubuntu 22.04)
- [ ] Install Docker & Docker Compose
- [ ] Configure PostgreSQL 15 (managed or self-hosted)
- [ ] Set up basic monitoring (htop, df, free)

### Phase 2: Application Deployment (Week 3-4)
- [ ] Create docker-compose.yml with all services
- [ ] Build Docker images for each service
- [ ] Deploy to VPS via docker-compose up
- [ ] Verify all services running

### Phase 3: Persistence & Monitoring (Week 5-6)
- [ ] Configure PostgreSQL backups (daily snapshots)
- [ ] Set up Prometheus + Grafana
- [ ] Create monitoring dashboards
- [ ] Test backup/restore procedures

### Phase 4: Scaling Preparation (Week 7-8)
- [ ] Design multi-VPS architecture (if needed)
- [ ] Prepare Kubernetes manifests (for future migration)
- [ ] Document scaling procedures
- [ ] Set up load testing environment

---

## Validation

### Success Criteria

1. **Availability**: 99.0% monthly uptime (REQ-901)
2. **Performance**: Episode processing within 24 hours
3. **Cost**: Stay within ¥8,000/month VPS budget
4. **Scalability**: Support 5 concurrent episodes
5. **Reliability**: Recovery from failure <4 hours

### Validation Method

1. **Uptime Monitoring**: Synthetic checks every 5 minutes, 99.0% SLO
2. **Performance Tracking**: Monitor episode processing time percentiles
3. **Cost Tracking**: Monitor DigitalOcean billing monthly
4. **Load Testing**: Test with 5 concurrent episode pipelines
5. **Disaster Recovery**: Monthly backup restore test

---

## Related Requirements

- REQ-501: Infrastructure & API Reliability
- REQ-901: Monthly Uptime (99.0%)
- REQ-902: Code Coverage (80%+)
- REQ-903: Monthly Cost (<¥8,000 infrastructure)

---

## Related ADRs

- ADR-005: Message Queue Selection
- ADR-006: Database Selection
