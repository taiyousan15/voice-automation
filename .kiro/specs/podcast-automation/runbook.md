# Incident Response Runbook - Podcast Automation System

**Last Updated**: 2026-02-11

**Version**: 1.0

**Status**: Ready for Operations

---

## 0. Quick Reference

### On-Call Contacts

| Role | Phone | Slack | Email |
|------|-------|-------|-------|
| On-Call Engineer | [TBD] | #podcast-ops | [TBD] |
| Engineering Lead | [TBD] | @eng-lead | [TBD] |
| Product Manager | [TBD] | @product-lead | [TBD] |

### Critical Links

- **Monitoring Dashboard**: https://grafana.podcast.local/dashboard/podcast-main
- **Alerting Console**: https://prometheus.podcast.local/alerts
- **Application Logs**: https://logs.podcast.local/podcast-*
- **Status Page**: https://status.podcast.example.com/

---

## 1. Severity Definitions

| Severity | Definition | Impact | Initial Response | Resolution Target |
|----------|-----------|--------|-----------------|-------------------|
| **SEV1** | Complete service outage, data loss risk, customer-facing failure | 100% loss of service | 15 minutes | 4 hours |
| **SEV2** | Major functionality down, >25% SLO impact | Significant degradation | 30 minutes | 8 hours |
| **SEV3** | Partial degradation, <25% SLO impact | Limited impact | 1 hour | 24 hours |
| **SEV4** | Minor issue, cosmetic/non-critical | No service impact | 4 hours | 1 week |

---

## 2. Initial Incident Response

### 2.1 Discovery & Assessment (First 5 minutes)

```
Incoming Alert
    ↓
Confirm Alert (not false positive)
    ↓
Assess Severity (1-4)
    ↓
Open Incident Channel & Page On-Call
    ↓
Gather Context (logs, metrics, recent changes)
```

### 2.2 Communication Template

**Slack Message**:
```
🚨 INCIDENT: [SEVERITY] [Service]: [Brief description]

Detected: [Time]
Status: Investigating
Estimate: [TBD]

On-call: @[name]
War room: [Google Meet link]

Updates: Every 15 min if SEV1/2, every hour if SEV3, daily if SEV4
```

### 2.3 Initial Investigation Checklist

- [ ] Confirm alert is not false positive (check 3 metrics)
- [ ] Determine severity (1-4) based on SLO impact
- [ ] Identify most likely root cause
- [ ] Check recent deployments (git log --oneline -5)
- [ ] Review error rates and latency trends
- [ ] Check external API status pages
- [ ] Gather team context in #podcast-ops

---

## 3. Common Issues & Resolution

### 3.1 HIGH LATENCY (P95 > 120 minutes)

**Symptoms**:
- Grafana shows P95 latency spike
- Alert: "HighLatency" triggered
- Episodes not delivered by 18:00 JST deadline

**Diagnosis**:

```bash
# Check which stage is slow
kubectl logs -n podcast orchestrator-* --tail=100 | grep duration

# View latency breakdown (Prometheus)
# Graph: pipeline_stage_duration_seconds_bucket (all stages)

# Common causes:
# 1. External API slow (NewsData.io, Claude, ElevenLabs)
# 2. Database query slow (N+1 query or missing index)
# 3. Pod resource contention (CPU/memory throttling)
# 4. Network latency to external services
```

**Resolution (Priority Order)**:

**Priority 1** (Immediate - 5 min):
```bash
# Check external API status
curl -s https://status.elevenlabs.io | grep -i operational
curl -s https://status.newsdata.io | grep -i operational

# If external API slow:
# - Activate circuit breaker (automatically done)
# - Fall back to Ollama for TTS
# - Use cached data where possible
```

**Priority 2** (Fast fix - 10 min):
```bash
# Check database connections
psql -h postgres.podcast.svc.cluster.local -U podcast -c "\
  SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check for slow queries
psql -h postgres.podcast.svc.cluster.local -U podcast -c "\
  SELECT query, calls, mean_time FROM pg_stat_statements \
  WHERE mean_time > 1000 ORDER BY mean_time DESC LIMIT 10;"

# If query slow:
# - Kill long-running queries (see 3.5)
# - Restart services if connection pool exhausted
```

**Priority 3** (Medium effort - 20 min):
```bash
# Check pod resource usage
kubectl top pods -n podcast

# If CPU/memory high:
kubectl describe node <node-name>  # Check node capacity
kubectl rollout restart deployment/orchestrator -n podcast
```

**Recovery Confirmation**:
- [ ] P95 latency < 120 min (check Grafana)
- [ ] Episodes generating normally (check logs)
- [ ] No new latency alerts for 10 min

---

### 3.2 HIGH ERROR RATE (> 1%)

**Symptoms**:
- Alert: "HighErrorRate" triggered
- Pipeline errors visible in logs
- Error budget burning rapidly

**Root Causes**:

```bash
# View recent errors
kubectl logs -n podcast orchestrator-* --tail=200 | grep ERROR

# Check error rate by stage
# Graph: pipeline_errors_total / pipeline_runs_total (per stage)

# Common causes:
# 1. Script generation failure (Claude API timeout)
# 2. TTS synthesis failure (ElevenLabs quota exceeded)
# 3. Database connection failure
# 4. Distribution API failures (Spotify, YouTube)
```

**Resolution**:

```bash
# Step 1: Identify failing stage
kubectl logs -n podcast <pod-name> --tail=100 | grep -i error

# Step 2: Check stage-specific logs
kubectl logs -n podcast script-generator-* | tail -50  # Check Claude API
kubectl logs -n podcast tts-engine-* | tail -50        # Check ElevenLabs
kubectl logs -n podcast distributor-* | tail -50       # Check APIs

# Step 3: Check external service status
curl https://status.openai.com  # Claude API status
curl https://status.elevenlabs.io  # ElevenLabs status
curl https://developer.spotify.com/status  # Spotify API status

# Step 4: If API quota exceeded
# Contact API provider for temporary limit increase
# Edit config to reduce request rate:
kubectl set env deployment/data-collector -n podcast \
  NEWSDATA_BATCH_SIZE=5 \
  APIFY_BATCH_SIZE=3
```

**Recovery Confirmation**:
- [ ] Error rate < 1% for 10 min
- [ ] No new error alerts
- [ ] Latest episodes succeeded
- [ ] Error budget recovering

---

### 3.3 DATABASE CONNECTION FAILURE

**Symptoms**:
- "connection refused" in logs
- All services unable to connect to PostgreSQL
- Grafana shows no data points

**Diagnosis**:

```bash
# Check PostgreSQL pod status
kubectl get pod postgres-0 -n podcast -o wide

# Check PostgreSQL logs
kubectl logs postgres-0 -n podcast --tail=100

# Try connecting
psql -h postgres.podcast.svc.cluster.local -U podcast -d podcast -c "SELECT 1"

# If connection refused:
# 1. Check pod is running: kubectl describe pod postgres-0
# 2. Check PVC is mounted: kubectl get pvc -n podcast
# 3. Check network connectivity: kubectl exec -it orchestrator-0 -- \
#    nc -zv postgres.podcast.svc.cluster.local 5432
```

**Resolution (Priority Order)**:

**If pod crashed**:
```bash
# Check error
kubectl logs postgres-0 -n podcast --previous

# Restart pod
kubectl delete pod postgres-0 -n podcast
# Pod will be recreated (StatefulSet handles this)

# Wait for recovery
kubectl wait --for=condition=Ready pod/postgres-0 -n podcast --timeout=300s
```

**If disk full**:
```bash
# Check PVC usage
kubectl exec postgres-0 -n podcast -- df -h /var/lib/postgresql/data

# If full:
# 1. Delete old backups: rm -rf /var/lib/postgresql/backups/*
# 2. Truncate logs: TRUNCATE TABLE postgres_log;
# 3. Restart PostgreSQL
```

**If port conflict**:
```bash
# Check if port 5432 is in use on node
ssh <node-name>
netstat -tlnp | grep 5432

# If conflict: redeploy PostgreSQL to different node
kubectl set node-selector postgres-0 -n podcast \
  kubernetes.io/hostname=<different-node>
```

**Recovery Confirmation**:
- [ ] PostgreSQL pod running: `kubectl get pod postgres-0`
- [ ] Can connect: `psql ... SELECT 1`
- [ ] No connection errors in logs
- [ ] Services reconnecting normally

---

### 3.4 OUT OF MEMORY

**Symptoms**:
- Pod killed with "OOMKilled" status
- Grafana shows memory usage approaching limit
- Latency spike then pod restarts

**Diagnosis**:

```bash
# Check which pod is OOMKilled
kubectl get pods -n podcast -o jsonpath='{.items[*].status.containerStatuses[*].state.terminated.reason}' | grep -i oomkilled

# Get details
kubectl describe pod <pod-name> -n podcast

# Check memory limit vs actual usage
kubectl top pod <pod-name> -n podcast
kubectl get pod <pod-name> -n podcast -o jsonpath='{.spec.containers[0].resources.limits.memory}'

# Check pod logs
kubectl logs <pod-name> -n podcast --previous
```

**Resolution**:

**Immediate (5 min)**:
```bash
# Increase memory limit
kubectl set resources deployment/tts-engine -n podcast \
  --limits=memory=8Gi,cpu=2

# Trigger rollout to get new pods with higher memory
kubectl rollout restart deployment/tts-engine -n podcast
```

**Root cause investigation (10 min)**:
```bash
# Check for memory leak
kubectl logs <pod-name> -n podcast | grep -i "memory\|cache\|buffer"

# Is service loading too much into memory?
# - Check if caching large datasets
# - Check if accumulating data structures
# - Check for connection leaks

# If code issue: plan code review + fix in next sprint
```

**Prevention**:
```bash
# Increase monitoring
# Add metric: memory_usage_percent
# Add alert: if > 80% for 5 min

# Auto-scale by memory
kubectl patch deployment tts-engine -n podcast -p \
  '{"spec":{"template":{"metadata":{"annotations":{"memory-scale-trigger":"true"}}}}}'
```

**Recovery Confirmation**:
- [ ] Pod running (not killed)
- [ ] Memory usage normal (< 70% of limit)
- [ ] Service responsive
- [ ] No repeated restarts

---

### 3.5 CPU THROTTLING

**Symptoms**:
- Latency spike
- CPU usage at 100%
- Services slow but not crashed

**Resolution**:

```bash
# Check CPU usage
kubectl top pod -n podcast

# Check if CPU limited
kubectl describe pod <pod-name> -n podcast | grep "cpu"

# Increase CPU limit
kubectl set resources deployment/script-generator -n podcast \
  --limits=cpu=2,memory=4Gi

# Check if process busy
kubectl exec <pod-name> -n podcast -- ps aux | grep -E "python|ollama"

# If Ollama busy: restart TTS pod to flush inference cache
kubectl restart deployment/tts-engine -n podcast

# If PyTorch model busy: add timeout
kubectl set env deployment/script-generator -n podcast \
  CLAUDE_TIMEOUT_SECONDS=30
```

---

### 3.6 EXTERNAL API QUOTA EXCEEDED

**Symptoms**:
- Error: "Rate limit exceeded" from NewsData.io or Claude
- Alert: "ExternalAPIRateLimit" triggered
- New episodes cannot be generated

**Resolution**:

**NewsData.io Quota Exceeded**:
```bash
# Check current usage (dashboard or API)
curl "https://newsdata.io/api/1/latest?apikey=<key>" | grep -i quota

# Reduce request rate
kubectl set env deployment/data-collector -n podcast \
  NEWSDATA_BATCH_SIZE=3 \
  NEWSDATA_BATCH_DELAY_SECONDS=2

# Wait for quota reset (usually next calendar month)
# Or upgrade to higher tier
```

**Claude API Quota Exceeded**:
```bash
# Check token usage in Claude dashboard
# If exceeded: contact Anthropic for temporary limit increase
# Or switch to Ollama fallback (automatic)

# Reduce token count
kubectl set env deployment/script-generator -n podcast \
  CLAUDE_MAX_TOKENS=4000 \
  CLAUDE_TEMPERATURE=0.5  # Reduce creativity/length

# Monitor fallback usage
kubectl logs -n podcast script-generator-* | grep -i "ollama\|fallback"
```

**ElevenLabs Quota Exceeded**:
```bash
# Check usage in ElevenLabs dashboard
# Switch to fallback TTS (MeloTTS)
kubectl set env deployment/tts-engine -n podcast \
  TTS_PRIMARY=ollama \
  TTS_SECONDARY=elevenlabs

# Reduce character count (shorten scripts)
kubectl set env deployment/script-generator -n podcast \
  MAX_SCRIPT_LENGTH=8000  # characters

# Monitor fallback quality
# (Listeners will notice slightly different voice quality)
```

---

### 3.7 SECURITY INCIDENT

**Symptoms**:
- Unauthorized access attempt detected
- API keys exposed in logs
- Malicious episode content generated

**Immediate Response** (Do NOT delay):

```bash
# Step 1: Isolate affected system
kubectl scale deployment <affected-service> -n podcast --replicas=0

# Step 2: Preserve evidence
kubectl logs <affected-pod> > incident-$(date +%s).log
kubectl describe pod <affected-pod> > incident-$(date +%s).yaml

# Step 3: Notify security team
# Slack: @security-team + email security@company.com

# Step 4: Rotate credentials
# If API key exposed:
kubectl set env deployment/<service> -n podcast \
  API_KEY="<NEW-KEY>" --overwrite

# Or regenerate token:
psql -h postgres.podcast.svc.cluster.local -U podcast -c \
  "UPDATE admin_tokens SET revoked=true WHERE token='<exposed-token>';"

# Step 5: Audit logs for compromise
# Check CloudTrail, Kubernetes audit logs, PostgreSQL audit logs
```

**Investigation**:
```bash
# How did attacker gain access?
# - Check RBAC policies
# - Check network policies
# - Check application authentication

# What damage was done?
# - Check episode modification timestamps
# - Check API key usage logs
# - Check distributed episodes
```

**Recovery**:
```bash
# If malicious episodes distributed:
# - Contact podcast platforms (Apple, Spotify)
# - Request takedown/delisting
# - Notify listeners via official channels

# If data exfiltrated:
# - Notify affected users (email, website)
# - Force password resets
# - Monitor for secondary attacks

# Post-mortem required: Why was this possible?
# - Add SIEM/WAF rules
# - Implement secrets rotation
# - Review access policies
```

---

## 4. Rollback Procedures

### 4.1 Application Rollback

**If broken deployment causes issue**:

```bash
# Check recent deployments
kubectl rollout history deployment/orchestrator -n podcast

# View specific revision
kubectl rollout history deployment/orchestrator -n podcast --revision=10

# Rollback to previous version
kubectl rollout undo deployment/orchestrator -n podcast

# Or rollback to specific revision
kubectl rollout undo deployment/orchestrator -n podcast --to-revision=9

# Monitor rollout
kubectl rollout status deployment/orchestrator -n podcast -w

# Verify old version working
kubectl get pods -n podcast
kubectl logs -n podcast orchestrator-* | tail -20
```

### 4.2 Database Migration Rollback

**If schema migration breaks application**:

```bash
# List migrations
ls -la alembic/versions/ | tail -10

# Find migration ID that caused issue
cat alembic/versions/[current_version].py | head -20

# Rollback
alembic downgrade -1  # Back one version

# Or specific version
alembic downgrade [migration-id]

# Verify database schema
psql -h postgres.podcast.svc.cluster.local -U podcast -c \
  "\dt"  # List tables

# Check data integrity
psql -h postgres.podcast.svc.cluster.local -U podcast -c \
  "SELECT COUNT(*) as episode_count FROM episodes;"
```

### 4.3 Configuration Rollback

**If configuration change breaks system**:

```bash
# Check current config
kubectl get configmap podcast-config -n podcast -o yaml > current-config.yaml

# View previous config (if version controlled)
git show HEAD~1:k8s/configmap.yaml > previous-config.yaml

# Apply previous config
kubectl apply -f previous-config.yaml

# Restart pods to pick up old config
kubectl rollout restart deployment/orchestrator -n podcast
kubectl rollout restart deployment/script-generator -n podcast
kubectl rollout restart deployment/tts-engine -n podcast
```

---

## 5. Recovery Checklist

After resolving any incident, verify recovery with this checklist:

### Immediate Recovery (First 30 min):

- [ ] Root cause identified
- [ ] Service responding normally
- [ ] Latency back to baseline
- [ ] Error rate < 1%
- [ ] No critical alerts active
- [ ] Latest episodes processing correctly

### Communication & Documentation (1 hour):

- [ ] Update incident Slack channel with resolution
- [ ] Update status page: resolved ✓
- [ ] Notify customers of incident window
- [ ] Schedule post-mortem (within 24 hours)

### Post-Incident (24-48 hours):

- [ ] Post-mortem completed (see template below)
- [ ] Root cause prevention implemented (or planned)
- [ ] Monitoring/alerting improved
- [ ] Documentation updated
- [ ] All action items assigned

---

## 6. Post-Mortem Template

**Required for all SEV1/2, optional for SEV3**

```markdown
# Post-Mortem: [Incident Name]

**Date**: [YYYY-MM-DD]
**Duration**: [HH:MM]
**Severity**: SEV-[1-4]
**Owner**: [Name]

## Timeline

| Time | Event |
|------|-------|
| HH:MM | Alert triggered: [Description] |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Service recovered |

## Root Cause

[What happened?]

## Impact

- Downtime: [X minutes]
- Affected users: [X%]
- Error budget burned: [X%]

## Contributing Factors

1. [Factor 1: e.g., "No circuit breaker for external API"]
2. [Factor 2: e.g., "Slow deployment rollback process"]
3. [Factor 3: e.g., "Insufficient monitoring for this scenario"]

## Resolution

[What was done to fix it?]

## Action Items (Prevent Recurrence)

| Item | Owner | Due Date |
|------|-------|----------|
| [Action 1] | [Name] | [Date] |
| [Action 2] | [Name] | [Date] |

## Lessons Learned

- What went well?
- What could be improved?
- Changes to processes/monitoring/documentation?
```

---

## 7. Escalation Matrix

| Condition | Action | Timeline |
|-----------|--------|----------|
| SEV1 + Not resolved in 30 min | Page engineering lead | Immediately |
| SEV1 + Not resolved in 1 hour | Page director of engineering | Immediately |
| SEV1 + Not resolved in 2 hours | Page VP of engineering + CTO | Immediately |
| Error budget exhausted | Planning meeting to reduce features | 1 day |
| 3 SEV1 incidents in 30 days | Full system audit + architecture review | 1 week |

---

## 8. On-Call Handoff Checklist

When transitioning on-call responsibilities:

- [ ] Review recent incidents (last week)
- [ ] Check current error budget status
- [ ] Verify all contacts/links are correct
- [ ] Review any open action items from post-mortems
- [ ] Do a test alert (pagerduty test)
- [ ] Walk through a scenario together (first time)

---

## 9. Appendix: Useful Commands

```bash
# Pod/Container commands
kubectl get pods -n podcast                              # List pods
kubectl describe pod <name> -n podcast                   # Details
kubectl logs <name> -n podcast --tail=100                # View logs
kubectl exec -it <name> -n podcast -- bash               # Shell access
kubectl delete pod <name> -n podcast                     # Force restart

# Database commands
psql -h postgres.podcast.svc.cluster.local -U podcast -c "SELECT * FROM episodes LIMIT 10;"
psql -h postgres.podcast.svc.cluster.local -U podcast -c "SHOW max_connections;"

# Monitoring
kubectl port-forward svc/prometheus 9090:9090 -n podcast # Access Prometheus
kubectl port-forward svc/grafana 3000:3000 -n podcast    # Access Grafana

# Network diagnostics
kubectl run debug --image=busybox --rm -it -- sh
# Inside debug pod:
curl http://orchestrator.podcast.svc.cluster.local:8000/health
nslookup postgres.podcast.svc.cluster.local
```

---

**Last Review**: 2026-02-11
**Next Review**: 2026-05-11
