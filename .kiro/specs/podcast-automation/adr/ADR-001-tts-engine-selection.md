# ADR-001: TTS Engine Selection Strategy (MeloTTS + ElevenLabs Hybrid)

**Status**: Accepted

**Date**: 2026-02-11

**Decision Makers**: Architecture Committee

---

## Context

The podcast automation system requires high-quality text-to-speech capability across multiple daily episodes (30-45 minutes per theme). Key constraints:

- **Quality Requirements**: Professional audio quality (90-95 points) for premium tier
- **Cost Sensitivity**: Flexible pricing models (¥0-1,600/month for zero-cost tier, ¥38,700-44,000/month for premium)
- **Availability**: 99.0% monthly uptime requirement (REQ-901)
- **Scale**: Up to 3 daily episodes initially, scaling to 10+ themes
- **Languages**: Japanese primary, English secondary
- **Latency**: <5 seconds audio generation required (REQ-405)

The system must serve two market segments:
1. **Startup Tier**: Zero-cost or minimal-cost operations
2. **Enterprise Tier**: Premium quality with professional reliability

---

## Decision

Adopt a **hybrid TTS strategy** with fallback chain:

```
┌─────────────────────────────────────────────────┐
│ Script Ready                                     │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ Primary: ElevenLabs Pro (if premium tier)       │
│ - Quality: 95/100 (natural prosody)             │
│ - Latency: 3-5 seconds                          │
│ - Cost: ¥14,850/month (Pro plan)                │
│ - Features: Custom voice models, emotion sync   │
└────────┬────────────────────────────────────────┘
         │
    [ERROR/TIMEOUT?]
         │
         ▼
┌─────────────────────────────────────────────────┐
│ Fallback: ElevenLabs Creator (mid-tier)         │
│ - Quality: 85/100 (good natural voice)          │
│ - Latency: 5-8 seconds                          │
│ - Cost: ¥22,000/month                           │
│ - Rate limit: 200k chars/month                  │
└────────┬────────────────────────────────────────┘
         │
    [ERROR/QUOTA EXCEEDED?]
         │
         ▼
┌─────────────────────────────────────────────────┐
│ Last Resort: MeloTTS-Japanese (OSS)             │
│ - Quality: 75/100 (acceptable for fallback)     │
│ - Latency: 2-3 seconds                          │
│ - Cost: ¥0 (self-hosted)                        │
│ - Deployment: Docker container, GPU optional    │
│ - Limitation: No emotion/accent control         │
└────────┬────────────────────────────────────────┘
         │
    [FALLBACK EXHAUSTED?]
         │
         ▼
┌─────────────────────────────────────────────────┐
│ Queue for Manual Intervention                   │
│ - Alert: Send to operations dashboard           │
│ - Retry: Exponential backoff (max 3 attempts)   │
│ - SLA: Recovery within 2 hours                  │
└─────────────────────────────────────────────────┘
```

### Tier-Based Implementation

**Pattern 1 (Zero-Cost Tier)**:
```
Script → MeloTTS-Japanese (Docker) → MP3 → RSS → Distribution
Cost: ¥0/month (self-hosted)
Quality: 70-80/100
Limitation: Basic voice, no prosody variation
```

**Pattern 2 (Premium Quality Tier)**:
```
Script → [ElevenLabs Pro] → [ElevenLabs Creator] → [MeloTTS] → MP3 → Distribution
Cost: ¥38,700/month
Quality: 90-95/100
Benefit: Professional voice, emotion sync, speaker consistency
```

### Technical Details

```python
# Pseudocode for TTS selection logic
class TTSEngine:
    async def synthesize(script: str, tier: str) -> AudioFile:
        if tier == "PREMIUM":
            try:
                return await elevenlabs_pro.synthesize(script)
            except TimeoutError:
                logger.warn("EL Pro timeout, trying Creator")
            except QuotaExceededError:
                logger.warn("EL Pro quota exceeded")

            try:
                return await elevenlabs_creator.synthesize(script)
            except TimeoutError:
                logger.warn("EL Creator timeout, trying MeloTTS")
            except QuotaExceededError:
                logger.warn("EL Creator quota exceeded")

        try:
            return await melotts_japanese.synthesize(script)
        except Exception as e:
            logger.error(f"All TTS engines failed: {e}")
            queue_for_manual_intervention(script, error=e)
            raise TTSFailureError()
```

---

## Consequences

### Benefits ✅

1. **Cost Flexibility**
   - Zero-cost path for startups: ¥0/month with MeloTTS
   - Scalable premium path: ¥38,700-44,000/month with ElevenLabs Pro
   - Gradual migration: Start with MeloTTS, upgrade to ElevenLabs as revenue increases

2. **Quality & Reliability**
   - Premium quality (95/100) for enterprise customers
   - Graceful degradation: System continues functioning even if primary TTS fails
   - Multiple fallback chains prevent service outages (99.0% uptime)

3. **Latency & Performance**
   - ElevenLabs: 3-8 seconds generation (within <5 sec SLO via queue pre-processing)
   - MeloTTS: 2-3 seconds generation (faster for fallback scenarios)
   - Parallel processing: Multiple episodes can be synthesized simultaneously

4. **Operational Simplicity**
   - Single integration point: TTSEngine abstraction hides implementation details
   - No vendor lock-in: Can swap TTS provider without changing application code
   - Circuit breaker pattern: Automatic failover without manual intervention

5. **Risk Mitigation**
   - Single TTS provider dependency eliminated (reduces business risk)
   - Graceful degradation prevents cascading failures
   - Manual intervention queue ensures no content is lost

### Drawbacks ⚠️

1. **Implementation Complexity**
   - Circuit breaker logic adds ~300 lines of code
   - Requires monitoring 3 different TTS engines simultaneously
   - Error handling matrix becomes complex (7 failure modes)

2. **Quality Variance**
   - Fallback to MeloTTS may produce noticeably different voice between episodes
   - Customer experience inconsistency if ElevenLabs quota exhausted mid-month
   - Voice continuity breaks if switching between engines

3. **Operational Overhead**
   - 3 separate monitoring dashboards (EL Pro, EL Creator, MeloTTS)
   - Quota management required for ElevenLabs accounts
   - MeloTTS GPU capacity planning needed for peak load

4. **Cost Optimization Trade-offs**
   - Hybrid approach costs more than single provider (EL Pro + MeloTTS infrastructure)
   - Character-based pricing (EL) vs episode-based cost unclear
   - Potential waste if using expensive EL when MeloTTS would suffice

### Tradeoff Analysis

| Aspect | ElevenLabs Only | MeloTTS Only | Hybrid (Chosen) |
|--------|-----------------|--------------|-----------------|
| **Quality** | 95/100 | 75/100 | 95/100 (avg 90) |
| **Cost** | ¥38,700-44,000/month | ¥0/month | ¥38,700/month + ops cost |
| **Reliability** | Single point of failure | Stable (no API risk) | Multi-path fallback |
| **Latency** | 3-5 seconds | 2-3 seconds | 3-5 (primary) + fallback |
| **Uptime SLO** | 99.5% (provider) | 99.99% (self) | 99.0% system-wide |
| **Scalability** | API quota limits | Unlimited (self-hosted) | Scaled per tier |
| **Vendor Lock-in** | HIGH | NONE | LOW |
| **Operational Burden** | LOW (managed) | HIGH (self-hosted) | MEDIUM |

---

## Alternatives Considered

### ❌ Alternative 1: ElevenLabs Only (No Fallback)

**Concept**: Use exclusively ElevenLabs Pro for all tiers.

**Pros**:
- Simplest implementation
- Consistent voice quality across all episodes
- Professional support from ElevenLabs
- Voice cloning features available

**Cons**:
- Single point of failure (API outage = service down)
- Cost: ¥38,700/month for all customers (not viable for zero-cost tier)
- Quota limitations for high-volume customers
- Vendor lock-in (switching costs high)

**Why Rejected**: Does not support zero-cost tier requirement (REQ-900 specifies ¥0-1,600 budget). Single provider creates excessive business risk.

---

### ❌ Alternative 2: MeloTTS Only (No ElevenLabs)

**Concept**: Self-host MeloTTS-Japanese exclusively for all tiers.

**Pros**:
- Zero API costs (¥0/month)
- No vendor dependencies
- Unlimited character processing
- Full control over model and deployment

**Cons**:
- Quality: 70-80/100 (not suitable for premium customers)
- Requires GPU infrastructure (¥3,000-5,000/month)
- Voice is robotic, lacks prosody
- Model training/fine-tuning needed for better quality
- Maintenance burden (model updates, dependency management)

**Why Rejected**: Does not meet premium quality requirement (REQ-303 requires 80+ script quality, which needs professional TTS voice). GPU infrastructure cost approaches ElevenLabs pricing, eliminating cost advantage.

---

### ❌ Alternative 3: Google Cloud Text-to-Speech

**Concept**: Use Google Cloud TTS as primary, fallback to MeloTTS.

**Pros**:
- Reliable API (99.99% uptime)
- Good quality (85/100)
- Integrates with GCP ecosystem
- Free tier: 1M chars/month

**Cons**:
- Free tier insufficient for production (3 episodes × 10,000 words = 30k chars/day)
- Cost: ¥4,500-8,000/month for production volume
- Limited emotional/accent control
- Licensing restrictions (commercial use requires special agreement)

**Why Rejected**: Cost-quality tradeoff worse than ElevenLabs. No significant advantage over chosen hybrid approach. Doesn't solve zero-cost tier requirement.

---

### ❌ Alternative 4: Mix of Multiple API Providers (3+ TTS)

**Concept**: Use ElevenLabs + Google Cloud + Azure + MeloTTS with smart routing.

**Pros**:
- Maximum redundancy (4 independent providers)
- Cost optimization (choose cheapest per episode)
- Never blocked by single API quota

**Cons**:
- Exponentially complex routing logic
- Difficult to maintain voice consistency
- Monitoring and debugging becomes nightmare
- Operational expertise required for 4 platforms
- Cost overhead outweighs savings (overhead > savings)

**Why Rejected**: Over-engineered for problem at hand. Complexity cost not justified by benefits. Chosen hybrid (2 providers) provides sufficient redundancy.

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Set up ElevenLabs Pro account and credentials
- [ ] Deploy MeloTTS-Japanese Docker image with GPU
- [ ] Implement TTSEngine abstraction class
- [ ] Create unit tests for each TTS implementation

### Phase 2: Integration (Week 3-4)
- [ ] Implement circuit breaker pattern
- [ ] Add ElevenLabs API client with retry logic
- [ ] Implement fallback chain (El Pro → El Creator → MeloTTS)
- [ ] Add error tracking and alerting

### Phase 3: Testing & Validation (Week 5-6)
- [ ] Load test: 50 concurrent episodes per day
- [ ] Failure test: Simulate EL API timeout, quota exceeded
- [ ] Latency test: Measure P95 latency per engine
- [ ] Quality comparison: A/B test voice samples

### Phase 4: Monitoring & Operations (Week 7-8)
- [ ] Deploy Prometheus metrics (TTS latency, error rate, quota usage)
- [ ] Set up Grafana dashboards (per engine, per tier)
- [ ] Create runbook for TTS quota management
- [ ] Implement manual intervention queue monitoring

### Related Tasks
- [ ] TASK-405: Implement TTS abstraction layer
- [ ] TASK-406: Add circuit breaker for API resilience
- [ ] TASK-407: Create TTS monitoring dashboards
- [ ] TASK-408: Write TTS disaster recovery runbook

---

## Validation

### Success Criteria

1. **Quality**: Average voice quality >= 85/100 (validated via listening test)
2. **Latency**: P95 generation time <= 5 seconds (validated via monitoring)
3. **Availability**: System uptime >= 99.0% monthly (validated via SLO monitoring)
4. **Fallback**: All fallback chains tested and verified working
5. **Cost**: Stay within budget (<¥1,600/month zero-cost tier, <¥44,000/month premium)

### Validation Method

1. **Listening Tests**: Sample 20 episodes monthly, rate quality 1-100
2. **Load Testing**: Simulate peak load (10 episodes/hour), measure latency percentiles
3. **Chaos Engineering**: Inject failures (API timeout, quota exceeded), verify fallback
4. **Cost Tracking**: Monitor API usage, verify charges within budget
5. **User Feedback**: Collect listener ratings on voice quality

### Review Schedule

- **Monthly**: Review metrics (quality, latency, cost) and adjust provider allocation
- **Quarterly**: Re-evaluate alternative TTS providers, benchmark against current solution
- **Annually**: Strategy review, consider new TTS technologies

---

## Related Requirements

- **REQ-303**: AI-Driven Script Generation & Quality (links to TTS quality)
- **REQ-305**: Error Handling & Fallback Mechanisms
- **REQ-400**: Audio Generation & Multi-Platform Distribution
- **REQ-405**: TTS Generation Latency (<5 seconds)
- **REQ-501**: Infrastructure & API Reliability
- **REQ-901**: Monthly Uptime Requirement (99.0%)
- **REQ-903**: Monthly Operating Cost (<¥1,600 zero-cost, <¥44,000 premium)

---

## Related ADRs

- ADR-002: Primary Data Source Selection
- ADR-003: Script Generation Approach (Claude vs Ollama)
- ADR-005: Deployment Platform Selection

---

## Glossary

- **MADR**: Markdown Any Decision Records format
- **Circuit Breaker**: Design pattern for handling failures gracefully
- **Prosody**: Natural intonation and rhythm in speech
- **SLO**: Service Level Objective (target uptime/latency)
- **EL**: ElevenLabs API
- **TTS**: Text-to-Speech synthesis
- **GPU**: Graphics Processing Unit (for MeloTTS acceleration)
