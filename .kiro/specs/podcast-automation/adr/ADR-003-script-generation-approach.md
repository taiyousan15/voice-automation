# ADR-003: Script Generation Approach (Claude Haiku vs Local Ollama)

**Status**: Accepted

**Date**: 2026-02-11

**Decision Makers**: Architecture Committee

---

## Context

The podcast system requires converting news articles into engaging 30-45 minute podcast scripts daily. Key constraints:

- **Script Quality**: 70-90 points (mid to high quality, engaging narration)
- **Latency**: <2 minutes script generation per episode (REQ-303)
- **Cost**: ¥0-3,000/month AI model costs (within budget)
- **Language**: Japanese primary, English secondary support
- **Tone**: Conversational but authoritative (suitable for podcast)
- **Availability**: 99.0% script generation success (REQ-901)
- **Customization**: Per-theme tone adjustment (philosophy, business, AI)

---

## Decision

Adopt a **hybrid script generation strategy** with Claude Haiku as primary, local Ollama as fallback:

```
Primary: Claude Haiku API (¥3,000/month)
  ↓ [Error/Timeout]
Fallback: Ollama Llama 3.1 (Local, ¥0)
  ↓ [Error]
Last Resort: Template Generation (Manual review needed)
```

### Tier-Based Implementation

**Pattern 1 (Zero-Cost Tier)**:
```
Article → Ollama (Llama 3.1 8B, Docker)
  + Simple prompt template
  = ¥0/month AI cost
  → Script quality: 70-75/100
  → Generation time: 5-10 minutes
```

**Pattern 2 (Premium Quality Tier)**:
```
Article → Claude Haiku (API)
  + Advanced prompting (persona, tone, structure)
  = ¥3,000/month (200k tokens/month @ 0.015¥/1k)
  → Script quality: 85-90/100
  → Generation time: 2-3 minutes
  → Fallback to Ollama if Claude fails
```

---

## Consequences

### Benefits ✅

1. **Quality Consistency**: Claude delivers 85-90/100 quality with sophisticated prompting
2. **Cost Efficiency**: ¥3,000/month Haiku with ¥0 Ollama fallback (best ratio)
3. **Latency Performance**: 2-3 min Claude primary, 5-10 min Ollama fallback
4. **Reliability**: Multi-tier fallback ensures no script generation failures
5. **Flexibility**: Prompt engineering enables per-theme tone customization

### Drawbacks ⚠️

1. **Dual Model Maintenance**: Must maintain Claude and Ollama API clients
2. **Quality Variance**: Fallback scripts noticeably lower quality (70-75 vs 85-90)
3. **GPU Infrastructure**: Ollama needs GPU (¥3-5k/month if renting)
4. **Prompt Engineering**: Requires expertise to optimize prompts
5. **Token Cost Unpredictability**: Variable token usage per article length

### Tradeoff Analysis

| Aspect | Claude Only | Ollama Only | GPT-4 | Hybrid (Chosen) |
|--------|------------|-----------|-------|-----------------|
| **Quality** | 85-90 | 70-75 | 95+ | 85-90 ✓ |
| **Cost** | ¥5,000 | ¥3,000 | ¥50,000 | ¥3,000 ✓ |
| **Latency** | 2-3 min | 5-10 min | 1-2 min | 2-3 min ✓ |
| **Reliability** | 99.9% API | 99% self | 99.95% | 99.5% ✓ |
| **Fallback** | ❌ | ❌ | ❌ | ✅ |

---

## Alternatives Considered

### ❌ Alternative 1: Claude Only

**Pros**: Simplest, highest consistent quality
**Cons**: Single point of failure, cost ¥5,000 (exceeds budget)
**Why Rejected**: Business risk from single point of failure, cost exceeds target

### ❌ Alternative 2: Ollama Only

**Pros**: Zero cost, unlimited usage
**Cons**: Lower quality (15 points less), longer latency (5-10 min)
**Why Rejected**: Quality gap too significant for premium tier, total cost with GPU similar to Claude

### ❌ Alternative 3: GPT-4 Turbo

**Pros**: Highest quality (95+/100)
**Cons**: Cost ¥50,000/month (10x budget), overkill for use case
**Why Rejected**: Diminishing returns, cost not justified

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Set up Claude API account and credentials
- [ ] Create per-theme prompt templates
- [ ] Implement ScriptGenerator abstraction class
- [ ] Write unit tests for script generation

### Phase 2: Claude Integration (Week 3-4)
- [ ] Implement Claude Haiku API client
- [ ] Add token counting and cost tracking
- [ ] Implement script validation (readability, coverage, tone)
- [ ] Add per-theme quality scoring

### Phase 3: Ollama Integration (Week 5-6)
- [ ] Deploy Ollama with Llama 3.1 8B
- [ ] Configure Docker container for production
- [ ] Implement Ollama API client with circuit breaker
- [ ] Test fallback chain (Claude → Ollama → Template)

### Phase 4: Validation & Optimization (Week 7-8)
- [ ] Load test: 100 scripts/day for 14 days
- [ ] Quality review: Manual sampling and scoring
- [ ] Prompt optimization: Per-theme quality tuning
- [ ] Cost analysis: Track actual token usage vs. budget

---

## Validation

### Success Criteria

1. **Quality**: Average ≥ 80/100 (readability, tone, coverage)
2. **Latency**: P95 ≤ 5 minutes (validated via monitoring)
3. **Availability**: Success rate ≥ 99.0% (validated via logging)
4. **Cost**: Stay within ¥3,000/month (validated via API tracking)
5. **Fallback**: Ollama successfully handles Claude failures

---

## Related Requirements

- REQ-201: Podcast Template Analysis
- REQ-301: AI-Driven Script Generation
- REQ-302: Quality Validation
- REQ-303: Script Quality Metrics (80+/100)
- REQ-901: Monthly Uptime (99.0%)
- REQ-903: Monthly Cost

---

## Related ADRs

- ADR-001: TTS Engine Selection
- ADR-002: Primary Data Source Selection
- ADR-004: Deployment Platform
