# Service Level Objectives (SLO) - Podcast Automation System

**Date**: 2026-02-11

**Version**: 1.0

**Status**: Draft (Requires Review)

**Based on Google SRE Principles** and podcast automation requirements

---

## Executive Summary

This document defines measurable reliability targets for the podcast automation system:

- **Availability SLO**: 99.0% monthly uptime (max 7.2 hours downtime/month)
- **Latency SLO**: P95 < 120 minutes episode processing
- **Error Rate SLO**: < 1% pipeline failures
- **Error Budget**: 0.33% (≈ 72 minutes/month)
- **Error Budget Policy**: Dynamic engagement controls based on burn rate

---

## 1. SLI Definitions (Service Level Indicators)

Service Level Indicators are **measurable** metrics that directly reflect user experience.

### 1.1 Availability SLI

**Definition**: Request success rate (episodes successfully generated and distributed)

**Measurement**:
```promql
# Prometheus query
(
  rate(episodes_generated_total{status="success"}[5m]) +
  rate(episodes_distributed_total{status="success"}[5m])
) / (
  rate(episodes_total[5m])
) * 100

# Alternative: HTTP endpoint success rate
(
  rate(http_requests_total{status=~"2.."}[5m])
) / (
  rate(http_requests_total[5m])
) * 100
```

**Time Series**: Calculated as rolling 5-minute average

**Target Period**: 30 calendar days (rolling window)

**Exclusions**:
- Planned maintenance (scheduled Sunday 02:00-03:00 JST)
- External API downtime (NewsData.io, Claude API > 30 min) - excluded if documented
- User misconfiguration errors - not counted as service failure

---

### 1.2 Latency SLI

**Definition**: Episode processing latency (time from article collection to distribution-ready audio)

**Measurement**:
```promql
# Episode generation latency (P50, P95, P99)
histogram_quantile(0.95,
  rate(episode_generation_duration_seconds_bucket[5m])
)

# Full pipeline latency (collection → distribution)
histogram_quantile(0.95,
  rate(pipeline_total_duration_seconds_bucket[5m])
)
```

**Buckets**: [1s, 10s, 30s, 60s, 120s, 300s, 600s, 1800s]

**Phases**:
1. **Data Collection** (target P95: 5 min)
   - NewsData.io API call
   - Deduplication and trust scoring
   - Cache results

2. **Analysis** (target P95: 10 min)
   - Template selection
   - Article ranking
   - Metadata extraction

3. **Script Generation** (target P95: 5 min)
   - Claude Haiku API call
   - Fallback to Ollama if needed
   - Validation

4. **TTS Synthesis** (target P95: 30 min)
   - ElevenLabs API call or MeloTTS local
   - Audio file generation
   - Storage upload

5. **Distribution** (target P95: 10 min)
   - RSS generation
   - Spotify API upload
   - YouTube upload
   - Stand.fm distribution

**Total P95 Target**: ≤ 120 minutes

---

### 1.3 Error Rate SLI

**Definition**: Pipeline failures per total episodes processed

**Measurement**:
```promql
# Episode pipeline error rate
rate(pipeline_errors_total[5m]) / rate(pipeline_runs_total[5m]) * 100

# By stage:
- Collection errors: 5% max acceptable
- Generation errors: 1% max acceptable
- Distribution errors: 2% max acceptable
```

**Error Categories**:
- **Transient**: Timeout, rate limit, temporary API outage (retryable)
- **Permanent**: Invalid input, schema mismatch, corrupted data
- **Operational**: Database connection failure, disk full

---

### 1.4 Script Quality SLI

**Definition**: Podcast script quality as rated by listening panel

**Measurement**:
```promql
# Quality scoring (0-100 scale)
histogram_quantile(0.5,
  rate(script_quality_score_bucket[24h])
)

# Thresholds:
- P50 >= 70: Acceptable
- P50 >= 80: Good
- P50 >= 90: Excellent
```

**Validation**: Monthly manual review of 30-50 random episodes by quality panel

---

### 1.5 API Dependency Health SLI

**Definition**: Availability of external APIs required for pipeline

**Measurement**:
```promql
# External API health
(
  rate(external_api_calls_total{status="success"}[5m])
) / (
  rate(external_api_calls_total[5m])
) * 100

# Per API:
- NewsData.io: >= 99.0%
- Claude API: >= 99.5%
- ElevenLabs: >= 99.0%
- Spotify API: >= 99.0%
```

**Health Check Frequency**: Every 5 minutes via synthetic request

---

### 1.6 Data Freshness SLI

**Definition**: Age of newest article in pipeline (freshness)

**Measurement**:
```promql
# Time since last article ingestion
max(time() - max(article_ingestion_timestamp))

# Target: >= 1 new article per theme per 12 hours
```

**Threshold**: Warning if no new articles in 24 hours

---

## 2. SLO Definitions (Service Level Objectives)

SLOs are **targets** for SLIs, used to drive operational decisions.

### 2.1 Availability SLO

| Metric | Value | Period | Notes |
|--------|-------|--------|-------|
| **Availability** | 99.0% | 30 days | REQ-901 compliance |
| **Downtime Budget** | 7.2 hours | 30 days | ~2.4 min/day acceptable |
| **P50 Availability** | 99.5% | weekly rolling | Target (aspirational) |

**Definition in EARS format**:
```
要件文(EARS): システムは月間99.0パーセント以上の可用性を維持しなければならない。
可用性は（稼働日数 / 30日）× 100で計算される。ダウン時間合計は月間7.2時間以内に
制限される。計画的メンテナンス（日曜02:00-03:00 JST）は除外される。
```

---

### 2.2 Latency SLO

| Metric | P50 | P95 | P99 | Period |
|--------|-----|-----|-----|--------|
| **Data Collection** | 2 min | 5 min | 10 min | Daily |
| **Script Generation** | 2 min | 5 min | 10 min | Daily |
| **TTS Synthesis** | 10 min | 30 min | 60 min | Daily |
| **Full Pipeline** | 20 min | 120 min | 180 min | Daily |

**Target**: P95 ≤ 120 min for full episode pipeline (collection → distribution)

**Justification**: Episodes collected by 12:00 JST must be ready for distribution by 18:00 JST (6-hour deadline), with 2-hour safety margin.

---

### 2.3 Error Rate SLO

| Metric | Target | Period |
|--------|--------|--------|
| **Overall Pipeline Error Rate** | < 1.0% | Daily |
| **Collection Error Rate** | < 5% | Daily |
| **Generation Error Rate** | < 1% | Daily |
| **Distribution Error Rate** | < 2% | Daily |

**Definition**:
```
요件문(EARS): 에피소드 생성 파이프라인의 오류율은 1% 미만이어야 한다.
오류는 재시도 불가능한 영구적 실패로 정의된다.
```

---

### 2.4 Script Quality SLO

| Metric | Target | Period | Method |
|--------|--------|--------|--------|
| **Script Quality P50** | ≥ 70/100 | Monthly | Listening panel |
| **Script Quality P75** | ≥ 80/100 | Monthly | Listening panel |
| **Acceptable Scripts** | ≥ 95% | Monthly | Scoring rubric |

---

## 3. Error Budget & Policy

### 3.1 Error Budget Calculation

```
Monthly Error Budget = 100% - SLO Target
                     = 100% - 99.0%
                     = 1.0%

= 1.0% × 30 days × 1440 min/day
= 432 minutes/month (7.2 hours)

= 1.0% × 720 hours/month
= 7.2 hours/month
```

**Interpretation**: System can tolerate 7.2 hours of downtime per month while meeting SLO.

### 3.2 Error Budget Burn Rate Levels

| Level | Remaining Budget | Action |
|-------|------------------|--------|
| **Green** (0-50% burned) | 3.6+ hours | Business as usual, normal development |
| **Yellow** (50-75% burned) | 1.8-3.6 hours | Risk-sensitive changes only, code review required |
| **Orange** (75-100% burned) | 0-1.8 hours | No new features, reliability focus only |
| **Red** (>100% burned) | < 0 hours | Incident mode, all hands on deck, post-mortem required |

### 3.3 Burn Rate Alert Policy

| Burn Rate | Time Window | Action | Alert Severity |
|-----------|-------------|--------|-----------------|
| **30x burn rate** | 5 min avg | Critical incidents in progress | CRITICAL |
| **10x burn rate** | 1 hour avg | Significant degradation | WARNING |
| **3x burn rate** | 6 hour avg | Trend toward budget exhaustion | INFO |
| **1x burn rate** | 30 day trend | On track to exhaust budget | INFO |

**Example**: If error rate is 30% (vs 1% SLO), that's 30x burn rate → alert immediately

### 3.4 Error Budget Policy Rules

1. **Weekly Review**: Check error budget consumption every Monday
2. **Risk Management**: No major deployments if budget < 50% remaining
3. **Feature Freeze**: If budget < 25% remaining, freeze new features for 2 weeks
4. **Post-Mortem**: Any budget exhaustion requires post-mortem and blameless review
5. **Overflow Policy**: Months with > 100% burn rate budget "carry over" to next month (max 2 months)

---

## 4. SLA Definitions (Service Level Agreements)

SLA is the **customer-facing guarantee** with penalties for non-compliance.

### 4.1 Service Level Agreement

**Service**: Podcast Automation Platform

**Availability SLA**: 99.0% monthly uptime

**Measurement Period**: 30 calendar days (rolling 30-day window)

**Service Credit Policy**:

| Availability % | Monthly Credit |
|-----------------|-----------------|
| < 99.0% ≥ 98.5% | 10% monthly fee |
| < 98.5% ≥ 98.0% | 25% monthly fee |
| < 98.0% | 50% monthly fee |

**Exclusions**:
- Planned maintenance (scheduled, announced 7 days in advance)
- External API provider outages (documented by provider)
- Customer misconfiguration or misuse
- Force majeure events
- DDoS or malicious attacks

---

## 5. Monitoring & Alerts

### 5.1 Prometheus Alerting Rules

```yaml
# Critical: Pod crash loop
- alert: PipelineCrashLoop
  expr: increase(pipeline_pod_restart_total[15m]) > 5
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Pipeline pod restarting repeatedly"

# Critical: Availability burn rate
- alert: HighBurnRate5m
  expr: |
    (1 - (rate(episodes_success_total[5m]) / rate(episodes_total[5m])))
    > 0.3
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "30x burn rate over last 5 minutes"

# Warning: Approach budget exhaustion
- alert: ErrorBudgetLow
  expr: error_budget_remaining_percent < 25
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Error budget < 25%, approaching exhaustion"

# Warning: Latency degradation
- alert: HighLatency
  expr: |
    histogram_quantile(0.95, pipeline_duration_seconds_bucket)
    > 120 * 60  # 120 minutes in seconds
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "P95 latency exceeds 120 minutes"

# Info: No new articles
- alert: StaleContent
  expr: (time() - max(article_ingestion_timestamp)) > 86400
  for: 30m
  labels:
    severity: info
  annotations:
    summary: "No new articles ingested in 24 hours"
```

### 5.2 Dashboard Components

**Top-level Dashboard**:
- Availability SLO gauge (current week, month, quarter)
- Error budget remaining (%) with trend
- Burn rate (last 24h, last 7d)
- Pipeline success rate (%)

**Detailed Dashboard**:
- Per-stage latency (P50, P95, P99)
- Error rate by stage
- External API health
- Queue depth and processing rate
- Database connection pool usage

**Debug Dashboard** (on-call only):
- All Prometheus metrics
- Service logs and traces
- Deployment history
- Configuration snapshots

---

## 6. SLO Review & Reporting

### 6.1 Daily Report

**Contents**:
- Availability yesterday (%)
- Error budget consumed yesterday (%)
- Current burn rate
- Critical alerts triggered
- P95 latency trend

**Distribution**: Slack #podcast-ops channel, 09:00 JST

### 6.2 Weekly Review

**Participants**: On-call engineer, product lead, one architect

**Duration**: 30 minutes

**Topics**:
- SLO status (green/yellow/orange/red)
- Major incidents (root cause analysis)
- Burn rate trend (extrapolation to month-end)
- Action items for next week

### 6.3 Monthly Review

**Participants**: Engineering team, product, operations, executives

**Duration**: 1 hour

**Topics**:
- Monthly SLO attainment (actual vs target)
- Error budget consumption analysis
- Top error categories and resolution
- Infrastructure changes and performance impact
- Lessons learned and process improvements

### 6.4 SLO Dashboard

**Public Dashboard**: Available to all stakeholders
- Current month availability (%)
- Error budget remaining
- Burn rate trend

**Internal Dashboard**: Available to engineering team
- Per-service SLIs and SLOs
- Detailed metrics for debugging
- Alert history

---

## 7. SLO Improvement Plan

### Phase 1 (Months 1-3): Meet SLO

**Target**: Consistently hit 99.0% availability

**Actions**:
- [ ] Implement Prometheus + Grafana monitoring
- [ ] Set up alerting rules and escalation
- [ ] Establish on-call rotation
- [ ] Create runbooks for common incidents

### Phase 2 (Months 4-6): Increase SLO

**Target**: Improve to 99.5% availability

**Actions**:
- [ ] Add database read replicas for resilience
- [ ] Implement circuit breakers for external APIs
- [ ] Add automated failover for critical components
- [ ] Reduce latency via caching optimizations

### Phase 3 (Months 7-12): Sustain Excellence

**Target**: Maintain 99.5%+ with high confidence

**Actions**:
- [ ] Implement chaos engineering testing
- [ ] Add multi-region deployment
- [ ] Optimize cost per SLO point
- [ ] Establish predictive alerting

---

## 8. Escalation Policy

| Level | Condition | Action | Time |
|-------|-----------|--------|------|
| **P1** | Availability < 95% (5x+ burn rate) | Page on-call immediately | 5 min |
| **P2** | Availability < 98% (2x+ burn rate) | Alert #podcast-ops, page if persistent | 30 min |
| **P3** | Latency P95 > 150 min or budget < 50% | Log in #podcast-ops | 1 hour |
| **Scheduled** | Budget < 25%, no incident | Planning meeting to reduce risk | 1 day |

---

## 9. Appendix: Industry Benchmarks

### 9.1 Typical SLOs by Service Type

| Service Type | Availability SLO | Typical SLA |
|--------------|------------------|------------|
| Consumer Services | 99.9%-99.95% | 99.5%-99.9% |
| Enterprise Apps | 99.5%-99.9% | 99.0%-99.5% |
| Batch Systems | 95%-99% | 90%-98% |
| **Podcast Automation** | **99.0%** | **98.5%** |

### 9.2 Error Budget Interpretation

```
99.0% SLO = 7.2 hours downtime/month budget
  └─ Allows for:
     - 1 major incident (4 hours) every 4 weeks
     - + 1 minor incident (2 hours) every 2 weeks
     - + Maintenance & upgrades (1.2 hours)
```

---

## 10. References

- [Google SRE Book - Monitoring Chapter](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [SLO & Error Budgets](https://sre.google/sre-book/error-budgets/)

---

## 11. Sign-Off

| Role | Name | Date | Approval |
|------|------|------|----------|
| SRE Lead | [TBD] | [TBD] | [ ] |
| Product Manager | [TBD] | [TBD] | [ ] |
| Engineering Lead | [TBD] | [TBD] | [ ] |

**Next Steps**:
1. Set up Prometheus + Grafana
2. Implement alerting rules
3. Establish on-call rotation
4. Create SLO dashboard
5. Run first weekly review
