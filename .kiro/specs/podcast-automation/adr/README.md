# Architecture Decision Records (ADR)

This directory contains all major architectural decisions for the podcast automation system, documented in MADR (Markdown Any Decision Records) format.

## Quick Reference

| ID | Title | Status | Created | Links to Requirements |
|----|-------|--------|---------|----------------------|
| **ADR-001** | TTS Engine Selection (MeloTTS + ElevenLabs Hybrid) | Accepted | 2026-02-11 | REQ-303, REQ-305, REQ-400, REQ-405, REQ-901, REQ-903 |
| **ADR-002** | Primary Data Source Selection (NewsData.io + Apify) | Accepted | 2026-02-11 | REQ-101, REQ-102, REQ-103, REQ-104, REQ-901, REQ-903 |
| **ADR-003** | Script Generation Approach (Claude Haiku + Ollama) | Accepted | 2026-02-11 | REQ-201, REQ-301, REQ-302, REQ-303, REQ-901, REQ-902, REQ-903 |
| **ADR-004** | Deployment Platform (VPS + Optional Cloud) | Accepted | 2026-02-11 | REQ-501, REQ-901, REQ-903 |
| **ADR-005** | Message Queue & Task Scheduling (APScheduler) | Accepted | 2026-02-11 | REQ-501, REQ-901 |
| **ADR-006** | Database Selection (PostgreSQL 15) | Accepted | 2026-02-11 | REQ-501, REQ-901 |
| **ADR-007** | Authentication & Authorization (JWT + Refresh Tokens) | Accepted | 2026-02-11 | REQ-501, REQ-902 |
| **ADR-008** | Audio Distribution Strategy (RSS-First Multi-Platform) | Accepted | 2026-02-11 | REQ-400, REQ-401, REQ-402, REQ-403, REQ-404, REQ-405, REQ-406 |

---

## ADR Descriptions

### ADR-001: TTS Engine Selection (Text-to-Speech)
**Problem**: Need high-quality voice synthesis for podcast episodes across cost-sensitive and premium tiers.

**Decision**: Hybrid approach with ElevenLabs Pro (primary) → ElevenLabs Creator (fallback) → MeloTTS (local fallback)

**Key Tradeoffs**:
- Quality: 95/100 (premium) vs 70/100 (fallback)
- Cost: ¥38,700/month (premium) vs ¥0/month (zero-cost)
- Reliability: Multi-tier fallback prevents single point of failure

**Implementation Status**: Ready for Phase 1

---

### ADR-002: Primary Data Source Selection
**Problem**: Need diverse, high-quality content from multiple domains (Philosophy/Business/AI).

**Decision**: Hierarchical sources: NewsData.io (primary) + Apify (YouTube/X) + Reddit (community)

**Key Tradeoffs**:
- Coverage: 75/100 average quality (blended across sources)
- Cost: ¥0-14,850/month (free tier to premium tier)
- Reliability: Fallback chain prevents single source failure

**Implementation Status**: Ready for Phase 1

---

### ADR-003: Script Generation Approach
**Problem**: Convert article content into engaging podcast scripts within 2-3 minutes.

**Decision**: Claude Haiku API (primary, ¥3,000/month) with Ollama fallback (local)

**Key Tradeoffs**:
- Quality: 85-90/100 (Claude) vs 70-75/100 (Ollama)
- Cost: ¥3,000/month (API) vs ¥0/month (self-hosted)
- Latency: 2-3 min (Claude) vs 5-10 min (Ollama)

**Implementation Status**: Ready for Phase 1

---

### ADR-004: Deployment Platform Selection
**Problem**: Host podcast system reliably with minimal operational overhead.

**Decision**: DigitalOcean VPS (¥8,000/month) with upgrade path to Kubernetes

**Key Tradeoffs**:
- Cost: ¥8,000/month (single VPS) vs ¥25k+ (Kubernetes)
- Scalability: 5 concurrent episodes (VPS) vs unlimited (K8s)
- Operations: Docker Compose (simple) vs K8s (complex)

**Implementation Status**: Ready for Phase 1

---

### ADR-005: Message Queue & Task Scheduling
**Problem**: Reliably schedule daily episode generation at consistent times.

**Decision**: APScheduler for predictable cron-like scheduling, Redis for peak load buffering

**Key Tradeoffs**:
- Simplicity: ¥0 cost (built-in) vs ¥5k+ (Celery + RabbitMQ)
- Scalability: Single machine vs distributed across multiple workers

**Implementation Status**: Ready for Phase 1

---

### ADR-006: Database Selection
**Problem**: Persist episodes, metadata, logs, and ensure data integrity.

**Decision**: PostgreSQL 15 (self-hosted on VPS)

**Key Tradeoffs**:
- Cost: ¥0 (self-hosted) vs ¥5k+ (managed RDS)
- Operations: Manual backups vs managed service
- Reliability: Fits relational data model perfectly

**Implementation Status**: Ready for Phase 1

---

### ADR-007: Authentication & Authorization
**Problem**: Secure admin dashboard and public API access.

**Decision**: JWT-based tokens with database-backed refresh tokens

**Key Tradeoffs**:
- Simplicity: Standard JWT (stateless) vs Session-based (stateful)
- Revocation: Can't revoke unexpired tokens (by design, acceptable tradeoff)

**Implementation Status**: Ready for Phase 1

---

### ADR-008: Audio Distribution Strategy
**Problem**: Deliver episodes to listeners across 5+ podcast platforms simultaneously.

**Decision**: RSS-first approach (Apple Podcasts, Spotify, YouTube) + Direct APIs (stand.fm, note.com, X)

**Key Tradeoffs**:
- Reach: 5+ platforms with single RSS feed vs custom integration
- Latency: RSS sync (24-48 hours) vs direct APIs (immediate)
- Cost: ¥0 infrastructure cost

**Implementation Status**: Ready for Phase 1

---

## Status Legend

- **Proposed**: Under review, not yet implemented
- **Accepted**: Approved, implementation planned or in progress
- **Deprecated**: No longer recommended, superseded by newer ADR
- **Superseded**: Replaced by another ADR (reference the new ADR)

---

## Implementation Roadmap

### Phase 1: MVP (Weeks 1-8)
All 8 ADRs guide implementation:
- ADR-001: ElevenLabs integration (primary), MeloTTS (fallback)
- ADR-002: NewsData.io + Reddit integration
- ADR-003: Claude Haiku integration + Ollama fallback
- ADR-004: DigitalOcean VPS deployment
- ADR-005: APScheduler configuration
- ADR-006: PostgreSQL schema design
- ADR-007: JWT authentication system
- ADR-008: RSS + direct API distribution

### Phase 2: Growth (Weeks 9-16)
- Scale to 10+ themes (evaluate ADR-004 for Kubernetes migration)
- Add Apify supplementary sources (ADR-002)
- Implement managed PostgreSQL (ADR-006)

### Phase 3: Optimization (Weeks 17+)
- Add Celery for distributed task processing (ADR-005 review)
- Implement distributed tracing (ADR-004)
- Add multi-region deployment (ADR-004)

---

## Decision Making Process

Each ADR follows this structure:

1. **Context**: Problem statement, constraints, requirements
2. **Decision**: Clear statement of what was chosen
3. **Consequences**: Benefits, drawbacks, tradeoffs
4. **Alternatives**: What was considered and why rejected
5. **Implementation**: Concrete steps to realize decision
6. **Related**: Links to requirements, other ADRs, dependencies

---

## Review & Update Process

1. **Monthly Review**: Check if decisions remain valid given new constraints
2. **Quarterly Evaluation**: Benchmark against new technologies/approaches
3. **Supersede When Needed**: If decision proves wrong, create new ADR + mark old as Superseded
4. **Document Lessons**: Update Related section as implementation reveals connections

---

## Related Documentation

- [Requirements](../requirements.md) - Functional & non-functional requirements
- [Design](../design.md) - C4 architecture model
- [Implementation Guide](../../docs/IMPLEMENTATION.md) - Step-by-step build guide
- [Runbook](../runbook.md) - Operational procedures
- [Threat Model](../threat-model.md) - Security analysis
