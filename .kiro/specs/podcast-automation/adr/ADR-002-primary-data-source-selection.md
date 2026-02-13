# ADR-002: Primary Data Source Selection (NewsData.io + Apify Hybrid)

**Status**: Accepted

**Date**: 2026-02-11

**Decision Makers**: Architecture Committee

---

## Context

The podcast system requires daily curated content from multiple domains (Philosophy/Business/AI) across Japanese and English sources. Key constraints:

- **Information Quality**: 60-80 points (mid to high quality content)
- **Freshness**: Latest news within 24 hours (REQ-101)
- **Coverage**: Multiple thematic sources (Reddit, news sites, YouTube)
- **Diversity**: Avoid content echo chambers, maintain balanced perspective
- **Availability**: 99.0% data collection uptime (REQ-901)
- **Cost**: ¥0-7,500/month for data sources (within overall budget)
- **API Reliability**: Handle rate limiting, API failures gracefully

---

## Decision

Adopt a **hierarchical data source strategy** with NewsData.io as primary, Apify for supplementary coverage:

```
┌──────────────────────────────────────────────────────────┐
│ Daily Curation Cycle (06:00 JST)                         │
└─────────────────────────┬────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌─────────┐      ┌──────────┐     ┌──────────┐
   │NewsData │      │ Apify    │     │Reddit    │
   │.io News │      │ YouTube/ │     │API       │
   │(Primary)│      │X Scraper │     │(Direct)  │
   └────┬────┘      └────┬─────┘     └────┬─────┘
        │                │                │
        │ [Collect 50-80 │ [Collect 20-30 │ [Collect 10-20
        │ articles]      │ videos/posts]  │ discussions]
        │                │                │
        └─────────────────┼─────────────────┘
                          │
                          ▼
        ┌────────────────────────────────────┐
        │ Deduplication & Trust Scoring      │
        │ - Remove duplicates                │
        │ - Filter by theme relevance        │
        │ - Score source credibility (1-10)  │
        └────────┬─────────────────────────┘
                 │
        ┌────────▼──────────────┐
        │ Select Top 3-5 Articles│ (REQ-104)
        │ per Theme per Day      │
        └────────┬───────────────┘
                 │
                 ▼
        ┌──────────────────────┐
        │ Script Generation    │
        │ (via Claude Haiku)   │
        └──────────────────────┘
```

### Tier-Based Implementation

**Pattern 1 (Zero-Cost Tier)**:
```
NewsData.io Free (5,000 requests/month)
  + Reddit API (free)
  + X Scraping (via external API: free tier)
  = ¥0/month data cost
  → 1 article/day per theme (3 themes = 3 articles/day)
```

**Pattern 2 (Premium Quality Tier)**:
```
NewsData.io Professional (¥7,500/month)
  + Apify Indie Plan (¥7,350/month for YouTube/X scraping)
  + Reddit API (free)
  = ¥14,850/month data cost
  → 5-10 articles/day per theme + video/tweet context
```

### Technical Architecture

```python
# Hierarchical data collection with fallback
class DataCollector:
    async def collect_daily_content(theme: str) -> List[Article]:
        sources = []

        # 1. Primary: NewsData.io (most reliable, curated)
        try:
            sources.extend(
                await newsdata_io.search(
                    query=theme,
                    sort_by="publish_time",
                    language=["en", "ja"],
                    limit=50
                )
            )
        except RateLimitError:
            logger.warn("NewsData.io rate limit, using cached results")
            sources.extend(cache.get_recent(theme))

        # 2. Supplement: Reddit discussions (community perspective)
        try:
            sources.extend(
                await reddit_api.search_posts(
                    subreddit=["philosophy", "business", "MachineLearning"],
                    query=theme,
                    limit=20
                )
            )
        except Exception:
            logger.warn("Reddit API error, continuing")

        # 3. Extended: Apify scrapers (YouTube, X, Medium)
        if premium_tier:
            try:
                sources.extend(
                    await apify.run_actor(
                        actor_id="youtube-search",
                        input={"searchQuery": theme}
                    )
                )
            except Exception:
                logger.warn("Apify run failed, continuing")

        # 4. Deduplication and trust scoring
        deduplicated = self.deduplicate(sources)
        scored = self.trust_score(deduplicated)

        # 5. Return top 3-5 articles per theme
        return sorted(scored, key=lambda x: x.trust_score)[:5]
```

---

## Consequences

### Benefits ✅

1. **Reliability & Redundancy**
   - Multiple data sources prevent single-source failures
   - NewsData.io provides curated, fact-checked content (higher quality)
   - Reddit/X provides grassroots perspectives and emerging discussions
   - System continues functioning if one source fails

2. **Coverage & Diversity**
   - NewsData.io: Traditional news (60% of content)
   - Apify (YouTube/X): Video essays and expert commentary (20%)
   - Reddit: Community discussions and alternative perspectives (20%)
   - Avoids content bubble, maintains balanced viewpoint

3. **Cost Efficiency**
   - NewsData.io Free: ¥0/month, sufficient for startup tier
   - Gradual upgrade path: Free → Professional (¥7,500) as traffic grows
   - Apify Indie (¥7,350) cheaper than premium alternatives like Webhose.io
   - Total cost stays within budget (<¥14,850/month)

4. **Quality Consistency**
   - NewsData.io guarantees fact-checking (reduces misinformation)
   - Trust scoring filters low-credibility sources
   - Deduplication ensures fresh content daily
   - Latency: Content available within 24 hours of publication

5. **Operational Simplicity**
   - Single API integration point (DataCollector abstraction)
   - Hierarchical fallback (primary → supplement → extended)
   - No complex multi-provider orchestration
   - Caching layer mitigates API quota issues

### Drawbacks ⚠️

1. **Dependency Complexity**
   - 4 separate API integrations increase maintenance burden
   - Different rate limits and quota models to manage
   - Error handling becomes matrix-like (multiple failure scenarios)

2. **Data Quality Variance**
   - Reddit discussions sometimes lack journalistic rigor
   - YouTube/X content requires additional filtering (clickbait detection)
   - Trust scoring algorithm may filter out valuable niche perspectives
   - Language detection may misidentify content language

3. **Operational Overhead**
   - Quota management required for NewsData.io and Apify
   - Monitoring 4 different API health statuses
   - Caching layer adds complexity
   - Deduplication algorithm requires tuning

4. **Cost Trade-offs**
   - Apify (¥7,350) adds 50% to data source cost
   - May not be fully utilized if NewsData.io provides sufficient coverage
   - Free tier insufficient for 10+ themes (requires Professional upgrade)

5. **Latency Considerations**
   - Apify scraping slower than API queries (2-5 min per run)
   - Multiple source collection adds total latency
   - Required to queue collection tasks (not real-time)

### Tradeoff Analysis

| Aspect | NewsData.io Only | Apify Only | Reddit Only | Hybrid (Chosen) |
|--------|------------------|-----------|-------------|-----------------|
| **Quality** | 80/100 (curated) | 70/100 (mixed) | 60/100 (variable) | 75/100 (blended) |
| **Coverage** | News only | Tech/media | Community | All domains ✓ |
| **Cost** | ¥0-7,500 | ¥7,350 | ¥0 | ¥0-14,850 |
| **Freshness** | 6-24 hours | 12-48 hours | Real-time | 6-24 hours |
| **Reliability** | 99.5% | 95% | 98% | 99.0% |
| **Diversity** | News-heavy | Tech-heavy | Community-heavy | Balanced ✓ |
| **Scalability** | API quota limit | Scalable | Rate limit | Scaled per tier |
| **Operational** | Medium | High | Low | Medium |

---

## Alternatives Considered

### ❌ Alternative 1: NewsData.io Only (No Supplements)

**Concept**: Use exclusively NewsData.io for all content.

**Pros**:
- Simplest implementation (single API)
- Highest data quality (fact-checked news)
- Best journalistic standards
- Lowest operational complexity

**Cons**:
- Limited to news domain (no video essays, grassroots discussion)
- Bias toward major news outlets (misses niche perspectives)
- Single point of failure (API outage = no new content)
- Premium tier required for adequate volume (¥7,500/month minimum)
- No cost-free option (violates zero-cost tier requirement)

**Why Rejected**: Does not provide diverse content perspectives required for engaging podcast. NewsData.io alone too expensive for zero-cost tier. Single source creates business risk.

---

### ❌ Alternative 2: Apify + Custom Scrapers Only

**Concept**: Use Apify for YouTube/X/Medium scraping, build custom scrapers for other sites.

**Pros**:
- Apify provides pre-built actors (faster development)
- Custom scrapers can target specific high-value sites
- More flexibility than API-only approach
- Lower fixed costs than buying multiple API subscriptions

**Cons**:
- High initial development cost (custom scrapers: 100+ hours)
- Web scraping brittle (site structure changes break scraper)
- Legal/ToS risks (scraping may violate terms of service)
- Maintenance burden high (each site requires separate maintenance)
- Quality control difficult (no fact-checking mechanism)
- Rate limiting risk (IP bans from scraped sites)

**Why Rejected**: High development and maintenance cost outweighs benefits. Web scraping legal/ethical concerns. NewsData.io + Apify provides better quality-to-cost ratio.

---

### ❌ Alternative 3: Reddit API Only (No News)

**Concept**: Use Reddit API exclusively for content discovery.

**Pros**:
- Free (no API costs)
- Real-time community discussions
- Organic engagement (people self-curate)
- Grassroots perspective

**Cons**:
- Quality highly variable (misinformation common on Reddit)
- Bias toward tech/programming communities (misses business/philosophy)
- No fact-checking (requires heavy filtering)
- Moderation challenges (toxic discussions possible)
- Limited to English (Japanese Reddit much smaller)
- Algorithm easily gamed (upvotes don't = quality)

**Why Rejected**: Insufficient content quality for professional podcast. Reddit alone cannot cover all three themes adequately. Requires too much manual curation/filtering.

---

### ❌ Alternative 4: Premium Data API (Webhose.io / ScraperAPI)

**Concept**: Use enterprise data APIs (Webhose.io, ScraperAPI, SerpAPI) instead of building hybrid.

**Pros**:
- Single unified API
- Comprehensive coverage (news + web + social)
- High data quality
- Enterprise support

**Cons**:
- Very expensive: ¥40,000-100,000/month
- Overkill for podcast use case
- Vendor lock-in
- Complex API with steep learning curve

**Why Rejected**: Cost (5-10x more expensive) not justified by benefits. NewsData.io + Apify provides sufficient functionality at lower cost.

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Set up NewsData.io Professional account (apply for free tier first)
- [ ] Set up Reddit API credentials (OAuth2)
- [ ] Implement DataCollector abstraction class
- [ ] Create unit tests for each source

### Phase 2: Integration (Week 3-4)
- [ ] Implement NewsData.io API client
- [ ] Implement Reddit API client
- [ ] Build deduplication algorithm (MD5 hash + cosine similarity)
- [ ] Build trust scoring system

### Phase 3: Testing & Caching (Week 5-6)
- [ ] Load test: Collect content for 3 themes daily for 30 days
- [ ] Failure test: Simulate each API failing, verify fallback works
- [ ] Quality test: Compare article quality across sources
- [ ] Implement Redis caching layer (24-hour TTL)

### Phase 4: Apify Integration (Week 7-8)
- [ ] Set up Apify account (Indie plan for premium tier)
- [ ] Configure YouTube search actor
- [ ] Configure X scraper actor
- [ ] Integrate into DataCollector (fallback after NewsData + Reddit)

### Related Tasks
- [ ] TASK-101: Implement NewsData.io integration
- [ ] TASK-102: Implement Reddit API integration
- [ ] TASK-103: Build deduplication and trust scoring
- [ ] TASK-104: Implement caching layer
- [ ] TASK-105: Add Apify integration (premium tier)

---

## Validation

### Success Criteria

1. **Quality**: Average article quality >= 70/100 (validated via manual review)
2. **Freshness**: 95% of content published within 24 hours (validated via timestamp)
3. **Availability**: Data collection success rate >= 99.0% (validated via logging)
4. **Diversity**: Coverage across all 3 themes >= 80% (validated via tag analysis)
5. **Cost**: Stay within budget (¥0/month zero-cost, ¥14,850 premium)

### Validation Method

1. **Quality Review**: Sample 50 articles monthly, rate relevance 1-100
2. **Freshness Tracking**: Monitor publish timestamp vs collection time
3. **Availability Metrics**: Track API errors and fallback activation
4. **Diversity Analysis**: Verify all themes covered daily
5. **Cost Tracking**: Monitor API usage, verify charges within budget

### Review Schedule

- **Weekly**: Review error logs, adjust trust scoring thresholds
- **Monthly**: Analyze article quality feedback, curate source blacklist
- **Quarterly**: Evaluate additional data sources (HN, Medium, product communities)

---

## Related Requirements

- **REQ-101**: Information Collection from Multiple Sources
- **REQ-102**: Deduplication & Credibility Assessment
- **REQ-103**: Template Selection & Ranking
- **REQ-104**: Article Relevance Filtering
- **REQ-901**: Monthly Availability (99.0%)
- **REQ-903**: Monthly Operating Cost

---

## Related ADRs

- ADR-001: TTS Engine Selection (data quality impacts podcast value)
- ADR-003: Script Generation Approach (uses data as input)
- ADR-004: Deployment Platform (data collection requires reliable scheduling)

---

## Glossary

- **NewsData.io**: Aggregated news API with 50,000+ sources
- **Apify**: Web scraping automation platform with pre-built actors
- **Trust Scoring**: Algorithm to rank source credibility
- **Deduplication**: Process to remove duplicate articles
- **Rate Limiting**: API provider throttles requests to prevent abuse
- **API Quota**: Maximum number of API calls allowed per month
