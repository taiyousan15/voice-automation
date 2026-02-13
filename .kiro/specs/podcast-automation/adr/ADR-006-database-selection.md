# ADR-006: Database Selection (PostgreSQL)

**Status**: Accepted

**Date**: 2026-02-11

**Decision Makers**: Architecture Committee

---

## Context

The podcast system requires persistent storage for episodes, metadata, API logs, and scheduling. Key constraints:

- **Data Volume**: 1,000+ articles/month, 100+ episodes/month initially
- **Relationships**: Complex data model (themes, episodes, sources, distribution logs)
- **Queries**: Reporting, analytics, feed generation
- **Consistency**: ACID guarantees for episode state
- **Cost**: ¥0-3,000/month database infrastructure
- **Scalability**: Support growth from 3 to 10+ themes

---

## Decision

Adopt **PostgreSQL 15** as primary relational database:

```
Data Model:
┌──────────┐  ┌──────────┐  ┌─────────┐  ┌────────────┐
│  THEME   │  │ EPISODE  │  │ SOURCE  │  │DIST_LOG    │
├──────────┤  ├──────────┤  ├─────────┤  ├────────────┤
│id        │  │id        │  │id       │  │id          │
│name      │  │theme_id→ │  │episode→ │  │episode_id→ │
│url_slug  │  │pub_date  │  │title    │  │platform    │
└──────────┘  │script    │  │url      │  │status      │
              │audio_url │  │score    │  │timestamp   │
              │status    │  └─────────┘  └────────────┘
              └──────────┘
```

### Technical Stack

```yaml
# PostgreSQL on VPS
version: 15
connection_pool: pgBouncer (25-100 connections)
backup: Daily snapshots (DigitalOcean managed)
replication: Optional (managed RDS for production)
python_orm: SQLAlchemy + Alembic migrations
```

---

## Consequences

### Benefits ✅

1. **Reliability**: ACID guarantees, proven data integrity
2. **Flexibility**: Complex queries, JSON support, full-text search
3. **Cost**: ¥0/month (self-hosted on VPS), ¥5k+ for managed RDS
4. **Scalability**: Easily handles millions of rows, can upgrade to RDS later
5. **Maturity**: Extensively tested, huge community support

### Drawbacks ⚠️

1. **Operational Burden**: Backups, upgrades, monitoring are manual
2. **Single Point of Failure**: No built-in replication (unless RDS)
3. **Performance at Scale**: May need optimization for 10M+ rows

---

## Alternatives Considered

### ❌ Alternative 1: MongoDB (NoSQL)

**Pros**: Flexible schema, horizontal scaling
**Cons**: Overkill for structured data, ACID limitations, higher cost
**Why Rejected**: Relational data model fits PostgreSQL better

### ❌ Alternative 2: DynamoDB (AWS)

**Pros**: Serverless, auto-scaling
**Cons**: Vendor lock-in, expensive for relational queries (¥5k+/month)
**Why Rejected**: Cost and lock-in not justified for this use case

### ❌ Alternative 3: SQLite (Lightweight)

**Pros**: Zero infrastructure, single file
**Cons**: Scaling limitations, no multi-user concurrency, backup complexity
**Why Rejected**: Not suitable for multi-service architecture

---

## Implementation Plan

### Phase 1: Schema Design (Week 1)
- [ ] Define data model (THEME, EPISODE, SOURCE, DIST_LOG tables)
- [ ] Set up migrations with Alembic
- [ ] Create indices for common queries
- [ ] Design backup strategy

### Phase 2: Deployment (Week 2)
- [ ] Install PostgreSQL 15 on VPS
- [ ] Configure backups (daily automated)
- [ ] Set up pgBouncer for connection pooling
- [ ] Create monitoring dashboards

---

## Related Requirements

- REQ-501: Infrastructure & API Reliability
- REQ-901: Monthly Uptime (99.0%)

---

## Related ADRs

- ADR-004: Deployment Platform Selection
- ADR-005: Message Queue Selection
