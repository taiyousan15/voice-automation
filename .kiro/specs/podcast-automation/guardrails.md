# AI Agent Guardrails & Constraints - Podcast Automation

**Date**: 2026-02-11

**Purpose**: Define boundaries and safety constraints for AI-driven components (Claude, Ollama, prompts)

---

## 1. Core Guardrails

### 1.1 Script Generation (Claude Haiku)

**Allowed Operations**:
- Generate podcast scripts from articles (≤ 10k tokens input)
- Summarize news/research content
- Create engaging narratives with consistent tone
- Rewrite content for different themes (philosophy/business/AI)

**Forbidden Operations**:
- ❌ Generate misinformation or disproven claims
- ❌ Create defamatory content about individuals/organizations
- ❌ Generate hateful, abusive, or discriminatory content
- ❌ Fabricate sources or attributions
- ❌ Process personal information without consent

**Approval Required For**:
- ⚠️ Scripts on controversial topics (politics, religion, controversial figures)
- ⚠️ Scripts with strong opinions or advocacy positions
- ⚠️ Scripts mentioning real people by name

**Validation Checkpoints**:
```python
class ScriptValidator:
    def validate(script: str) -> bool:
        checks = [
            not contains_fabrications(script),           # No made-up sources
            not contains_hate_speech(script),            # No discriminatory language
            contains_min_citations(script, min=3),       # At least 3 sources
            flesch_kincaid_score(script) <= 12,         # Readable level
            sentiment_score(script) in [-0.3, 0.3],     # Neutral-ish tone
        ]
        return all(checks)
```

---

### 1.2 Data Collection (NewsData.io, Apify, Reddit)

**Allowed Sources**:
- ✅ Established news organizations (Reuters, AP, BBC, major publications)
- ✅ Academic and research institutions (universities, research labs)
- ✅ Subject-matter experts (verified accounts, official channels)
- ✅ Community discussions (Reddit, forums with moderation)

**Forbidden Sources**:
- ❌ Known misinformation outlets (manually maintained blocklist)
- ❌ Satire/parody sites (without explicit marking as satire)
- ❌ Fake news and conspiracy theory sites
- ❌ AI-generated content (detect via fingerprinting)

**Trust Scoring Formula**:
```python
trust_score = (
    source_authority_score * 0.4 +    # Reuters > local blog
    recency_score * 0.2 +              # < 7 days old
    corroboration_score * 0.25 +       # Multiple sources confirm
    author_credibility_score * 0.15    # Verified authors
)

# Only articles with trust_score > 0.6 included in pipeline
```

---

### 1.3 Multi-Platform Distribution

**Allowed Platforms**:
- ✅ Apple Podcasts, Spotify, YouTube, stand.fm, note.com (official APIs)
- ✅ X (formerly Twitter) public announcements only
- ✅ Official RSS feeds

**Forbidden Actions**:
- ❌ Distribute to unlicensed/piracy platforms
- ❌ Bypass platform terms of service
- ❌ Manipulate metrics (fake downloads, artificial engagement)
- ❌ Spam or abusive distribution

**Content Filtering**:
- All episodes reviewed by human for final approval before distribution
- Automatic scan for prohibited content (see 1.1)
- Distribution blocked for rejected episodes (manual queue item)

---

## 2. Safety Constraints

### 2.1 Input Validation

```python
class InputValidator:
    def validate_article(article: Dict) -> bool:
        # Check for malicious input
        if len(article["content"]) > 50000:  # Max 50k chars
            return False
        if count_urls(article["content"]) > 20:  # Max 20 links
            return False
        if contains_sql_injection(article["content"]):
            return False
        if contains_xss_payload(article["content"]):
            return False
        return True
```

### 2.2 Output Validation

```python
class OutputValidator:
    def validate_script(script: str) -> bool:
        # Ensure script meets quality standards
        if len(script) < 7000:  # Too short
            return False
        if len(script) > 12000:  # Too long
            return False
        if contains_profanity(script) > 5:  # Max 5 profanities
            return False
        if plagiarism_score(script) > 0.15:  # Max 15% matching
            return False
        if toxic_language_score(script) > 0.1:  # Max 10% toxic
            return False
        return True
```

### 2.3 Rate Limiting & Quotas

| Resource | Limit | Period | Reason |
|----------|-------|--------|--------|
| Claude API calls | 100 calls | Per hour | Cost control, API limits |
| Ollama inference | 50 concurrent | N/A | GPU capacity |
| Article processing | 500 articles | Per day | Quality control, manual review |
| Distribution | 10 episodes | Per day | Platform limits, manual approval |

---

## 3. Human-in-the-Loop Checkpoints

### 3.1 Approval Workflow

```
Automated Generation
    ↓
Quality Validation (pass/fail automation)
    ↓
[HUMAN REVIEW REQUIRED]
Content Check: Accuracy, tone, appropriateness
    ↓
Approval Decision (approve/reject/request changes)
    ↓
[IF APPROVED] → Distribution
[IF REJECTED] → Manual queue for editor intervention
```

### 3.2 Escalation Matrix

| Condition | Action | Owner | Deadline |
|-----------|--------|-------|----------|
| Script fails quality checks | Manual review | Content editor | 2 hours |
| Low trust source | Verify independently | Researcher | 4 hours |
| Controversial topic | Legal review | Counsel | 24 hours |
| Failed distribution | Manual retry | Operations | 1 hour |

---

## 4. Monitoring & Compliance

### 4.1 Audit Logging

Every AI operation logged with:
- Timestamp, user, operation type
- Input content (first 500 chars)
- Output content (first 500 chars)
- Validation results (pass/fail + reasons)
- Human approvals/rejections

### 4.2 Compliance Checks

**Monthly**:
- [ ] Review 50 random generated scripts for quality
- [ ] Check trust scores match reality
- [ ] Verify no content policy violations

**Quarterly**:
- [ ] Test guardrail effectiveness (try to bypass them)
- [ ] Review logs for edge cases
- [ ] Update guardrails based on new risks

### 4.3 Incident Response

If guardrail violation detected:
1. Immediately stop automated generation
2. Quarantine affected content
3. Notify compliance team
4. Audit logs for root cause
5. Update guardrails to prevent recurrence
6. Resume operations only after fix verified

---

## 5. Guardrail Configuration

### 5.1 Forbidden Words/Phrases

```python
FORBIDDEN_TERMS = {
    "explicit": ["f*ck", "sh*t", "a**hole", ...],
    "hate_speech": ["slur1", "slur2", ...],
    "misinformation": ["fake vaccine evidence", "moon landing hoax", ...],
    "fabrication": ["according to nonexistent study", ...]
}

# Scan all generated content
for term in FORBIDDEN_TERMS.values():
    if any(term in script.lower() for term in term):
        raise GuardrailViolation(f"Contains forbidden term: {term}")
```

### 5.2 Prompt Constraints (Claude)

```python
SYSTEM_PROMPT = """
You are a podcast script writer. IMPORTANT CONSTRAINTS:

1. ONLY use facts from the provided article. NO fabrication.
2. If uncertain about fact, mark as [CITATION NEEDED]
3. NO political advocacy, NO hateful language, NO misinformation
4. Verify all claims are directly supported by source
5. Maintain balanced tone (avoid strong opinions)
6. Include citations for all statistics/quotes

FORBIDDEN:
- Creating content praising violence
- Spreading medical misinformation
- Defamation of real people/organizations
- Conspiracy theories marked as fact

If asked to violate these constraints, refuse clearly.
"""
```

---

## 6. Ethical Guidelines

### 6.1 Content Principles

1. **Truthfulness**: Facts must be verifiable and accurate
2. **Fairness**: Present multiple perspectives on controversial topics
3. **Respect**: Treat all individuals and groups with dignity
4. **Transparency**: Acknowledge sources and limitations
5. **Responsibility**: Consider potential harms of content

### 6.2 Special Categories

**Political Content**:
- Present multiple viewpoints fairly
- Avoid endorsing candidates/parties
- Mark opinion clearly as opinion

**Medical/Health Content**:
- Source from credible medical institutions
- Avoid medical advice (recommend consulting doctors)
- Debunk common health misinformation carefully

**Financial Content**:
- Disclaim: "Not financial advice"
- Present balanced view of investments
- Avoid promoting risky financial products

---

## 7. Future Enhancements

- [ ] Implement real-time fact-checking service
- [ ] Add sentiment analysis guardrails
- [ ] Integrate with bias detection models
- [ ] Implement user feedback loop for guardrail tuning

---

**Status**: Ready for Implementation

**Review Frequency**: Quarterly

**Last Updated**: 2026-02-11
