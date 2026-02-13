# ADR-005: Message Queue & Task Scheduling (APScheduler Primary)

**Status**: Accepted

**Date**: 2026-02-11

**Decision Makers**: Architecture Committee

---

## Context

The podcast system requires reliable daily episode scheduling and task execution. Key constraints:

- **Scheduling**: Predictable daily schedule (06:00 JST per theme)
- **Reliability**: At-least-once task execution (no lost episodes)
- **Latency**: Task execution within 2-4 hours (deadline 18:00 JST for distribution)
- **Cost**: ¥0-2,000/month queue infrastructure
- **Operational Complexity**: Minimize external dependencies
- **Scalability**: Support multiple concurrent tasks (10+ themes)

---

## Decision

Adopt **APScheduler for predictable scheduling** with **Redis queue for peak load**:

```
Daily Schedule (06:00 JST):
  APScheduler triggers workflow for each theme
  ↓
  DataCollector → AnalyzerScheduler → ScriptGeneratorQueue
  ↓
  Redis queue buffers tasks if backpressure
  ↓
  Workers process from queue (fan-out pattern)
  ↓
  Results → PostgreSQL → Distributor (18:00 deadline)
```

### Technical Architecture

```python
# APScheduler configuration
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

# Daily podcast generation per theme
for theme in ["philosophy", "business", "ai"]:
    scheduler.add_job(
        func=orchestrator.generate_episode,
        trigger=CronTrigger(hour=6, minute=0, timezone='Asia/Tokyo'),
        args=(theme,),
        id=f'daily-{theme}',
        name=f'Generate {theme} podcast',
        misfire_grace_time=3600  # 1 hour grace period
    )

scheduler.start()
```

---

## Consequences

### Benefits ✅

1. **Simplicity**: APScheduler built into Python, no external service
2. **Cost**: ¥0/month (no message queue infrastructure)
3. **Predictability**: Deterministic scheduling (no random delays)
4. **Sufficient for Current Scale**: Handles 3-5 concurrent tasks
5. **Observability**: Direct integration with application logging

### Drawbacks ⚠️

1. **Single Point of Scheduler**: If VPS restarts, missed tasks must be rescheduled
2. **No Distributed Scheduling**: Limited to single machine
3. **Task Persistence**: Lost if process crashes (unless checkpointed)
4. **No Cross-Server Coordination**: Can't scale beyond single VPS without modifications

---

## Alternatives Considered

### ❌ Alternative 1: Celery + RabbitMQ

**Pros**: Distributed task queue, excellent for scaling
**Cons**: ¥5k+ infrastructure cost, complex setup, overkill for 3 themes
**Why Rejected**: Over-engineered for initial scale, cost not justified

### ❌ Alternative 2: AWS SQS + Lambda

**Pros**: Managed service, auto-scaling, reliable
**Cons**: ¥3k+/month, vendor lock-in, not ideal for long-running tasks
**Why Rejected**: Cost and complexity exceed VPS approach

### ❌ Alternative 3: Pub/Sub (Google Cloud / AWS SNS)

**Pros**: Event-driven, scalable
**Cons**: Not designed for scheduled tasks, requires Lambda, adds complexity
**Why Rejected**: Wrong abstraction for predictable scheduling

---

## Implementation Plan

### Phase 1: APScheduler Setup (Week 1)
- [ ] Configure APScheduler with daily triggers (06:00 JST)
- [ ] Implement job persistence (optional SQLite backend)
- [ ] Add error handling and retry logic
- [ ] Set up task logging

### Phase 2: Redis Integration (Week 2)
- [ ] Deploy Redis on VPS
- [ ] Implement worker pool (4-8 workers)
- [ ] Add queue depth monitoring
- [ ] Configure backpressure handling

### Phase 3: Monitoring (Week 3)
- [ ] Track job success/failure rates
- [ ] Monitor queue depth and latency
- [ ] Create alerts for failed jobs
- [ ] Set up manual retry procedures

---

## Related Requirements

- REQ-501: Infrastructure & API Reliability
- REQ-901: Monthly Uptime (99.0%)

---

## Related ADRs

- ADR-004: Deployment Platform Selection
- ADR-006: Database Selection
