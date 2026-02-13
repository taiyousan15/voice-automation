# ADR-008: Audio Distribution Strategy (RSS-First Multi-Platform)

**Status**: Accepted

**Date**: 2026-02-11

**Decision Makers**: Architecture Committee

---

## Context

The podcast system must distribute episodes to listeners across multiple platforms. Key constraints:

- **Platforms**: Apple Podcasts, Spotify, YouTube, stand.fm, note.com, X (Twitter)
- **Delivery**: Daily episodes available by 18:00 JST
- **Format**: MP3 audio + metadata (title, description, artwork)
- **Cost**: ¥0-2,000/month for distribution infrastructure
- **Scalability**: Handle growth from 3 themes to 10+ themes
- **Reliability**: No lost episodes, retry logic for failed uploads

---

## Decision

Adopt **RSS-centric distribution** with **direct platform APIs** as supplement:

```
Episode Generation (16:00 JST)
  ↓
Store in PostgreSQL + S3/Object Storage
  ↓
Generate RSS feeds (per theme)
  ↓
┌─────────────────────────────────────────┐
│ RSS Distribution (automatic)            │
├─────────────────────────────────────────┤
│ Apple Podcasts: Submit RSS URL         │ (1x only)
│ Spotify: RSS ingestion via API         │ (auto-sync)
│ YouTube: Upload video + auto-publish   │
│ stand.fm: API upload (native format)   │
│ note.com: RSS embed or API             │
│ X (Twitter): Tweet notification        │
└─────────────────────────────────────────┘
  ↓
Verify upload success → Log to PostgreSQL
  ↓
Notify users (email, push, in-app)
```

### Technical Architecture

```python
# RSS generation per theme
class RSSGenerator:
    def generate_feed(theme: str) -> str:
        """Generate RSS 2.0 feed for theme."""
        episodes = Episode.find_by_theme(theme, limit=50)

        feed = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
          <channel>
            <title>{theme} Podcast</title>
            <link>https://podcast.example.com/{theme}</link>
            <description>Daily podcast about {theme}</description>
            <language>ja</language>

            {'\n'.join([
                f'''
                <item>
                  <title>{ep.title}</title>
                  <link>{ep.distribution_url}</link>
                  <pubDate>{ep.pub_date.rfc2822()}</pubDate>
                  <enclosure url="{ep.audio_url}" type="audio/mpeg" length="{ep.audio_size}"/>
                  <description>{ep.description}</description>
                  <guid>{ep.id}</guid>
                </item>
                '''
                for ep in episodes
            ])}
          </channel>
        </rss>
        """
        return feed

# Platform distribution
class DistributionManager:
    async def distribute_episode(episode: Episode):
        """Publish episode to all platforms."""

        # Step 1: Upload audio to storage
        audio_url = await upload_to_s3(episode.audio_file)

        # Step 2: Apple Podcasts (RSS only, no API)
        # First time: Submit RSS URL to Apple Podcasts Connect
        # Ongoing: RSS auto-updates

        # Step 3: Spotify (API)
        spotify_id = await spotify_api.upload_episode(
            podcast_id=SPOTIFY_PODCAST_ID,
            title=episode.title,
            audio_url=audio_url,
            description=episode.description
        )

        # Step 4: YouTube (API)
        youtube_id = await youtube_api.upload_video(
            title=episode.title,
            description=episode.description,
            video_file=generate_audio_video(episode.audio_file),
            playlist_id=YOUTUBE_PLAYLIST_ID
        )

        # Step 5: stand.fm (API)
        standfm_id = await standfm_api.create_episode(
            title=episode.title,
            description=episode.description,
            audio_url=audio_url
        )

        # Step 6: X (Twitter)
        await twitter_api.post_tweet(
            text=f"New {episode.theme} podcast episode: {episode.title}\n{audio_url}",
            media_url=episode.artwork_url
        )

        # Log distribution
        episode.distribution_logs.append(DistributionLog(
            platforms=['apple_podcasts', 'spotify', 'youtube', 'standfm', 'x'],
            status='published',
            timestamp=now()
        ))
        episode.save()
```

---

## Consequences

### Benefits ✅

1. **Simplicity**: RSS is standard, handles most platforms automatically
2. **Cost**: ¥0 infrastructure cost (RSS generation in application)
3. **Reach**: Covers 5 major podcast platforms + social media
4. **Reliability**: RSS ensures eventual consistency (retries built-in)
5. **Control**: Direct API for platforms requiring custom handling

### Drawbacks ⚠️

1. **Latency**: Apple Podcasts may take 24-48 hours to ingest RSS
2. **API Complexity**: Different APIs for each platform
3. **Error Handling**: Each platform has different failure modes
4. **Metadata**: Platform-specific metadata requirements (different field names)

---

## Alternatives Considered

### ❌ Alternative 1: Direct Platform APIs Only (No RSS)

**Pros**: Maximum control, faster updates
**Cons**: Must implement 5+ different APIs, higher maintenance
**Why Rejected**: RSS provides majority of benefits with less code

### ❌ Alternative 2: Podcast Distribution Service (Podbean, Anchor)

**Pros**: Handles multi-platform distribution automatically
**Cons**: ¥2k+ monthly cost, vendor lock-in, less control
**Why Rejected**: Cost and lock-in not justified for self-hosted solution

### ❌ Alternative 3: Email List Only (No Platform Distribution)

**Pros**: Direct audience relationship, no third-party dependency
**Cons**: Much smaller reach, requires list building effort
**Why Rejected**: Misses majority of potential listeners

---

## Implementation Plan

### Phase 1: RSS Generation (Week 1-2)
- [ ] Implement RSS 2.0 feed generation
- [ ] Upload static RSS feeds to S3/storage
- [ ] Test RSS validity with RSS validators
- [ ] Set up CORS headers for RSS access

### Phase 2: Platform Integrations (Week 3-6)
- [ ] Apple Podcasts: Manual submission (one-time)
- [ ] Spotify: Implement API integration
- [ ] YouTube: Implement video upload + playlist
- [ ] stand.fm: Implement API integration
- [ ] note.com: Implement RSS embed

### Phase 3: Social Media (Week 7)
- [ ] Twitter API: Post episode notifications
- [ ] Track engagement metrics

### Phase 4: Monitoring (Week 8)
- [ ] Track distribution success per platform
- [ ] Implement retry logic for failed uploads
- [ ] Create distribution dashboard

---

## Related Requirements

- REQ-400: Audio Generation & Multi-Platform Distribution
- REQ-401: Apple Podcasts Distribution
- REQ-402: Spotify Distribution
- REQ-403: YouTube Distribution
- REQ-404: stand.fm Distribution
- REQ-405: note.com Distribution
- REQ-406: X (Twitter) Distribution

---

## Related ADRs

- ADR-001: TTS Engine Selection (generates audio for distribution)
- ADR-003: Script Generation Approach
