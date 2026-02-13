# Phase 1 API 実装リファレンス
## Implementation Reference Guide with Code Examples

---

## 1. Circuit Breaker + Exponential Backoff テンプレート

### 汎用実装（TypeScript）

```typescript
// circuit-breaker.ts

interface CircuitBreakerConfig {
  failureThreshold: number;
  successThreshold: number;
  timeout: number; // milliseconds
  maxRetries: number;
  initialDelay: number; // milliseconds
}

type CircuitBreakerState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface CircuitBreakerStatus {
  state: CircuitBreakerState;
  failureCount: number;
  successCount: number;
  lastFailureTime?: Date;
  totalRequests: number;
  failedRequests: number;
}

export class CircuitBreaker<T> {
  private state: CircuitBreakerState = 'CLOSED';
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime?: Date;
  private totalRequests = 0;
  private failedRequests = 0;

  constructor(private config: CircuitBreakerConfig) {}

  async execute(
    operation: () => Promise<T>,
    fallback?: () => Promise<T> | T
  ): Promise<T> {
    this.totalRequests++;

    // Check circuit state
    if (this.state === 'OPEN') {
      if (this.shouldTransitionToHalfOpen()) {
        this.state = 'HALF_OPEN';
        this.successCount = 0;
      } else {
        this.failedRequests++;
        return this.executeFallback(fallback);
      }
    }

    // Execute with retry logic
    for (let attempt = 0; attempt < this.config.maxRetries; attempt++) {
      try {
        const result = await operation();

        // Success
        this.onSuccess();
        return result;

      } catch (error) {
        if (attempt < this.config.maxRetries - 1) {
          const delay = this.calculateBackoffDelay(attempt);
          await this.sleep(delay);
        } else {
          this.onFailure();
          this.failedRequests++;
          return this.executeFallback(fallback);
        }
      }
    }

    throw new Error('Circuit breaker execution failed');
  }

  private onSuccess(): void {
    this.failureCount = 0;

    if (this.state === 'HALF_OPEN') {
      this.successCount++;
      if (this.successCount >= this.config.successThreshold) {
        this.state = 'CLOSED';
        console.log('Circuit breaker transitioned to CLOSED');
      }
    }
  }

  private onFailure(): void {
    this.lastFailureTime = new Date();
    this.failureCount++;

    if (this.failureCount >= this.config.failureThreshold) {
      this.state = 'OPEN';
      console.log('Circuit breaker transitioned to OPEN');
    }
  }

  private shouldTransitionToHalfOpen(): boolean {
    if (!this.lastFailureTime) return true;

    const timeSinceLastFailure = Date.now() - this.lastFailureTime.getTime();
    return timeSinceLastFailure >= this.config.timeout;
  }

  private calculateBackoffDelay(attempt: number): number {
    const exponentialDelay = this.config.initialDelay * Math.pow(2, attempt);
    const jitter = Math.random() * 1000;
    return Math.min(exponentialDelay + jitter, 60000);
  }

  private async executeFallback(fallback?: () => Promise<T> | T): Promise<T> {
    if (!fallback) {
      throw new Error('Circuit breaker is OPEN, no fallback available');
    }

    const result = fallback();
    return result instanceof Promise ? result : Promise.resolve(result);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getStatus(): CircuitBreakerStatus {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
      totalRequests: this.totalRequests,
      failedRequests: this.failedRequests
    };
  }
}

// Usage Example
const newsDataBreaker = new CircuitBreaker({
  failureThreshold: 5,
  successThreshold: 3,
  timeout: 60000,
  maxRetries: 3,
  initialDelay: 1000
});

async function fetchNews() {
  return newsDataBreaker.execute(
    async () => {
      const response = await fetch('https://newsdata.io/api/1/news?...');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    },
    async () => {
      // Fallback: cache から取得
      return getNewsFromCache();
    }
  );
}
```

---

## 2. Rate Limit Management（レート制限管理）

### Request Queue パターン

```typescript
// rate-limit-manager.ts

interface RateLimitConfig {
  maxRequestsPerSecond: number;
  maxRequestsPer15Minutes: number;
  burstAllowance?: number; // 短時間での超過許容
}

class RateLimitManager {
  private requestQueue: Array<{ timestamp: number; id: string }> = [];
  private config: RateLimitConfig;

  constructor(config: RateLimitConfig) {
    this.config = config;
  }

  async waitIfNeeded(requestId: string): Promise<void> {
    this.cleanOldRequests();

    const now = Date.now();
    const oneSecondAgo = now - 1000;
    const fifteenMinutesAgo = now - 15 * 60 * 1000;

    // Count requests in different time windows
    const requestsLastSecond = this.requestQueue.filter(
      r => r.timestamp > oneSecondAgo
    ).length;

    const requestsLast15Min = this.requestQueue.filter(
      r => r.timestamp > fifteenMinutesAgo
    ).length;

    // Check limits
    if (requestsLastSecond >= this.config.maxRequestsPerSecond) {
      const oldestRecentRequest = this.requestQueue
        .filter(r => r.timestamp > oneSecondAgo)[0];
      const waitTime = 1000 - (now - oldestRecentRequest.timestamp);
      await this.sleep(waitTime);
    }

    if (requestsLast15Min >= this.config.maxRequestsPer15Minutes) {
      const oldestRecentRequest = this.requestQueue
        .filter(r => r.timestamp > fifteenMinutesAgo)[0];
      const waitTime = 15 * 60 * 1000 - (now - oldestRecentRequest.timestamp);
      await this.sleep(waitTime);
    }

    // Add request to queue
    this.requestQueue.push({ timestamp: now, id: requestId });
  }

  private cleanOldRequests(): void {
    const fifteenMinutesAgo = Date.now() - 15 * 60 * 1000;
    this.requestQueue = this.requestQueue.filter(
      r => r.timestamp > fifteenMinutesAgo
    );
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getStatus(): {
    queueLength: number;
    estimatedWaitTime: number;
  } {
    const now = Date.now();
    const oneSecondAgo = now - 1000;
    const fifteenMinutesAgo = now - 15 * 60 * 1000;

    const recentRequests = this.requestQueue.filter(
      r => r.timestamp > oneSecondAgo
    );
    const last15MinRequests = this.requestQueue.filter(
      r => r.timestamp > fifteenMinutesAgo
    );

    let estimatedWaitTime = 0;
    if (recentRequests.length >= this.config.maxRequestsPerSecond) {
      estimatedWaitTime = Math.max(
        estimatedWaitTime,
        1000 - (now - recentRequests[0].timestamp)
      );
    }
    if (last15MinRequests.length >= this.config.maxRequestsPer15Minutes) {
      estimatedWaitTime = Math.max(
        estimatedWaitTime,
        15 * 60 * 1000 - (now - last15MinRequests[0].timestamp)
      );
    }

    return {
      queueLength: this.requestQueue.length,
      estimatedWaitTime
    };
  }
}

// Usage
const rateLimiter = new RateLimitManager({
  maxRequestsPerSecond: 10,
  maxRequestsPer15Minutes: 300
});

async function makeApiCall(id: string) {
  await rateLimiter.waitIfNeeded(id);
  return fetch('https://api.example.com/...');
}
```

---

## 3. NewsData.io の詳細実装

### 本番環境対応実装

```typescript
// newsdata-client.ts

import fetch from 'node-fetch';
import { CircuitBreaker } from './circuit-breaker';
import { RateLimitManager } from './rate-limit-manager';

interface NewsDataConfig {
  apiKey: string;
  language: string; // 'ja' for Japanese
  country: string; // 'jp' for Japan
  enableCache: boolean;
  cacheExpiry: number; // milliseconds
}

class NewsDataClient {
  private circuitBreaker: CircuitBreaker<any>;
  private rateLimiter: RateLimitManager;
  private cache: Map<string, { data: any; expiry: number }> = new Map();
  private config: NewsDataConfig;

  constructor(config: NewsDataConfig) {
    this.config = config;

    // Circuit breaker: 5 failures to open, 60s timeout
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 5,
      successThreshold: 3,
      timeout: 60000,
      maxRetries: 3,
      initialDelay: 1000
    });

    // Rate limiter: 30 requests per 15 minutes (free tier)
    this.rateLimiter = new RateLimitManager({
      maxRequestsPerSecond: 2, // Conservative: 30/900s ≈ 0.033/s, but burst to 2/s
      maxRequestsPer15Minutes: 30
    });
  }

  async searchNews(query: string): Promise<any> {
    const cacheKey = `search_${query}`;

    // Try cache first
    if (this.config.enableCache) {
      const cached = this.getFromCache(cacheKey);
      if (cached) return cached;
    }

    return this.circuitBreaker.execute(
      async () => {
        // Rate limiting
        await this.rateLimiter.waitIfNeeded(cacheKey);

        // API call
        const response = await fetch(
          `https://newsdata.io/api/1/news?apikey=${this.config.apiKey}&q=${encodeURIComponent(query)}&language=${this.config.language}&country=${this.config.country}`,
          {
            headers: {
              'User-Agent': 'NewsAggregator/1.0'
            }
          }
        );

        if (response.status === 429) {
          // Rate limit: calculate wait time from header
          const retryAfter = response.headers.get('Retry-After') || '60';
          throw new Error(`Rate limited, retry after ${retryAfter}s`);
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Cache result
        if (this.config.enableCache) {
          this.setInCache(cacheKey, data);
        }

        return data;
      },
      async () => {
        // Fallback: return cached data if available
        const cached = this.cache.get(cacheKey);
        if (cached) {
          console.log('Using expired cache as fallback');
          return cached.data;
        }
        throw new Error('No fallback data available');
      }
    );
  }

  async searchNewsByCategory(category: string): Promise<any> {
    const cacheKey = `category_${category}`;

    if (this.config.enableCache) {
      const cached = this.getFromCache(cacheKey);
      if (cached) return cached;
    }

    return this.circuitBreaker.execute(
      async () => {
        await this.rateLimiter.waitIfNeeded(cacheKey);

        const response = await fetch(
          `https://newsdata.io/api/1/news?apikey=${this.config.apiKey}&category=${category}&language=${this.config.language}&country=${this.config.country}`,
          { headers: { 'User-Agent': 'NewsAggregator/1.0' } }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (this.config.enableCache) {
          this.setInCache(cacheKey, data);
        }

        return data;
      },
      async () => {
        const cached = this.cache.get(cacheKey);
        return cached?.data || null;
      }
    );
  }

  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key);

    if (!cached) return null;

    if (Date.now() > cached.expiry) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  private setInCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      expiry: Date.now() + this.config.cacheExpiry
    });
  }
}

// Usage
const newsData = new NewsDataClient({
  apiKey: process.env.NEWSDATA_API_KEY || '',
  language: 'ja',
  country: 'jp',
  enableCache: true,
  cacheExpiry: 5 * 60 * 1000 // 5 minutes
});

async function getJapaneseNews() {
  try {
    const results = await newsData.searchNews('AI技術');
    console.log(`Found ${results.results?.length || 0} articles`);
    return results;
  } catch (error) {
    console.error('Failed to fetch news:', error);
  }
}
```

---

## 4. Reddit API の詳細実装

```typescript
// reddit-client.ts

import { CircuitBreaker } from './circuit-breaker';

interface RedditPost {
  id: string;
  title: string;
  url: string;
  score: number;
  createdAt: Date;
  subreddit: string;
  confidence: number;
}

class RedditClient {
  private circuitBreaker: CircuitBreaker<RedditPost[]>;
  private accessToken?: string;
  private tokenExpiry?: Date;

  constructor(
    private clientId: string,
    private clientSecret: string,
    private userAgent: string
  ) {
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 5,
      successThreshold: 3,
      timeout: 60000,
      maxRetries: 3,
      initialDelay: 1000
    });
  }

  async getAuthToken(): Promise<string> {
    if (this.accessToken && this.tokenExpiry && Date.now() < this.tokenExpiry.getTime()) {
      return this.accessToken;
    }

    const response = await fetch('https://www.reddit.com/api/v1/access_token', {
      method: 'POST',
      auth: {
        username: this.clientId,
        password: this.clientSecret
      },
      data: { grant_type: 'client_credentials' },
      headers: { 'User-Agent': this.userAgent }
    });

    const data = await response.json() as any;
    this.accessToken = data.access_token;
    this.tokenExpiry = new Date(Date.now() + data.expires_in * 1000);

    return this.accessToken;
  }

  async fetchFromSubreddit(subreddit: string, limit: number = 50): Promise<RedditPost[]> {
    return this.circuitBreaker.execute(
      async () => {
        const token = await this.getAuthToken();

        const response = await fetch(
          `https://oauth.reddit.com/r/${subreddit}/new?limit=${limit}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'User-Agent': this.userAgent
            }
          }
        );

        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After');
          throw new Error(`Rate limit exceeded, retry after ${retryAfter}s`);
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json() as any;

        return data.data.children
          .filter((child: any) => !child.data.is_self) // Only links
          .map((child: any) => ({
            id: child.data.id,
            title: child.data.title,
            url: child.data.url,
            score: child.data.score,
            createdAt: new Date(child.data.created_utc * 1000),
            subreddit: child.data.subreddit,
            confidence: Math.min(0.9, Math.log(child.data.score + 1) / 10) // Score-based confidence
          }));
      },
      async () => {
        // Fallback: return empty list
        console.log('Reddit API unavailable, returning empty fallback');
        return [];
      }
    );
  }

  async fetchMultipleSubreddits(subreddits: string[]): Promise<RedditPost[]> {
    const results: RedditPost[] = [];

    for (const subreddit of subreddits) {
      const posts = await this.fetchFromSubreddit(subreddit, 30);
      results.push(...posts);
    }

    // Deduplicate by URL
    const seen = new Set<string>();
    return results.filter(post => {
      if (seen.has(post.url)) return false;
      seen.add(post.url);
      return true;
    });
  }
}

// Usage
const reddit = new RedditClient(
  process.env.REDDIT_CLIENT_ID || '',
  process.env.REDDIT_CLIENT_SECRET || '',
  'NewsAggregator/1.0 by myusername'
);

async function getJapaneseTrendingNews() {
  const subreddits = ['newsokuhou', 'japan', 'Technology'];
  const posts = await reddit.fetchMultipleSubreddits(subreddits);

  return posts.sort((a, b) => b.score - a.score).slice(0, 20);
}
```

---

## 5. エラーハンドリング・テンプレート

```typescript
// error-handler.ts

enum ErrorType {
  RateLimited = 'RATE_LIMITED',
  ServerError = 'SERVER_ERROR',
  ClientError = 'CLIENT_ERROR',
  NetworkError = 'NETWORK_ERROR',
  Timeout = 'TIMEOUT',
  Unknown = 'UNKNOWN'
}

interface ErrorContext {
  type: ErrorType;
  statusCode?: number;
  message: string;
  retryable: boolean;
  suggestedDelay?: number;
}

class ApiErrorHandler {
  static categorizeError(error: any, statusCode?: number): ErrorContext {
    // HTTP errors
    if (statusCode === 429) {
      return {
        type: ErrorType.RateLimited,
        statusCode,
        message: 'API rate limit exceeded',
        retryable: true,
        suggestedDelay: 60000
      };
    }

    if (statusCode && statusCode >= 500) {
      return {
        type: ErrorType.ServerError,
        statusCode,
        message: `Server error: ${statusCode}`,
        retryable: true,
        suggestedDelay: 5000
      };
    }

    if (statusCode === 408) {
      return {
        type: ErrorType.Timeout,
        statusCode,
        message: 'Request timeout',
        retryable: true,
        suggestedDelay: 3000
      };
    }

    if (statusCode && (statusCode === 400 || statusCode === 401 || statusCode === 403)) {
      return {
        type: ErrorType.ClientError,
        statusCode,
        message: `Client error: ${statusCode}`,
        retryable: false
      };
    }

    // Network errors
    if (error.code === 'ECONNREFUSED') {
      return {
        type: ErrorType.NetworkError,
        message: 'Connection refused',
        retryable: true,
        suggestedDelay: 5000
      };
    }

    if (error.code === 'ETIMEDOUT' || error.code === 'ESOCKETTIMEDOUT') {
      return {
        type: ErrorType.Timeout,
        message: 'Connection timeout',
        retryable: true,
        suggestedDelay: 3000
      };
    }

    // Default
    return {
      type: ErrorType.Unknown,
      message: error.message || 'Unknown error',
      retryable: false
    };
  }

  static shouldRetry(context: ErrorContext, attempt: number, maxAttempts: number): boolean {
    if (!context.retryable) return false;
    if (attempt >= maxAttempts) return false;

    return true;
  }

  static calculateDelay(context: ErrorContext, attempt: number): number {
    if (context.suggestedDelay) {
      return context.suggestedDelay;
    }

    // Exponential backoff
    const exponential = Math.pow(2, attempt) * 1000;
    const jitter = Math.random() * 1000;

    return Math.min(exponential + jitter, 60000);
  }
}

// Usage
async function makeApiCallWithErrorHandling(
  operation: () => Promise<any>,
  maxAttempts: number = 3
) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const statusCode = error.response?.status;
      const errorContext = ApiErrorHandler.categorizeError(error, statusCode);

      console.log(`Attempt ${attempt + 1} failed:`, errorContext.message);

      if (!ApiErrorHandler.shouldRetry(errorContext, attempt, maxAttempts)) {
        throw error;
      }

      const delay = ApiErrorHandler.calculateDelay(errorContext, attempt);
      console.log(`Waiting ${delay}ms before retry...`);

      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

---

## 6. Apify Actor の基本テンプレート

```javascript
// apify-actor-example.js

const Apify = require('apify');

Apify.main(async () => {
  // Input configuration
  const input = await Apify.getInput();
  const {
    startUrls = [],
    maxDepth = 1,
    maxPages = 100,
    proxyGroups = ['RESIDENTIAL'],
    waitTime = 3000
  } = input || {};

  console.log('Starting web scraper...');
  console.log(`Target URLs: ${startUrls.length}`);
  console.log(`Proxy type: ${proxyGroups.join(', ')}`);

  // Create crawler with automatic proxy rotation
  const crawler = new Apify.PuppeteerCrawler({
    // Proxy configuration (automatic rotation)
    useApifyProxy: true,
    apifyProxyGroups: proxyGroups,

    // Performance tuning
    maxConcurrency: 10,
    maxRequestsPerMinute: 60,
    maxRequestsPerCpuMinute: 120,

    // Page processing
    handlePageFunction: async ({ page, request, response }) => {
      console.log(`Processing: ${request.url}`);

      // Wait for dynamic content
      await page.waitForTimeout(waitTime);

      // Extract data
      const data = await page.evaluate(() => {
        return {
          title: document.title,
          url: window.location.href,
          headings: Array.from(document.querySelectorAll('h1, h2, h3'))
            .map(h => h.textContent)
            .slice(0, 5),
          paragraphs: Array.from(document.querySelectorAll('p'))
            .map(p => p.textContent.trim())
            .filter(p => p.length > 20)
            .slice(0, 3),
          links: Array.from(document.querySelectorAll('a'))
            .map(a => ({
              text: a.textContent.trim(),
              href: a.href
            }))
            .filter(l => l.text.length > 0)
            .slice(0, 10)
        };
      });

      // Save to dataset
      await Apify.pushData({
        ...data,
        scrapedAt: new Date().toISOString(),
        statusCode: response.status()
      });

      // Enqueue linked pages (if within depth limit)
      if (request.userData.depth < maxDepth) {
        const links = data.links.map(l => l.href);
        await Promise.all(
          links.map(url => crawler.addRequests(
            [{ url }],
            { forefront: false, userData: { depth: request.userData.depth + 1 } }
          ))
        );
      }
    },

    // Error handling
    handleFailedRequestFunction: async ({ request, error }) => {
      console.error(`Request failed: ${request.url}`, error.message);

      // Log failed request
      await Apify.pushData({
        url: request.url,
        error: error.message,
        scrapedAt: new Date().toISOString(),
        status: 'FAILED'
      });

      // Handle specific error types
      if (error.message.includes('429')) {
        // Rate limit: will retry automatically
        request.noRetry = false;
      } else if (error.message.includes('403') || error.message.includes('401')) {
        // Access denied: skip
        request.noRetry = true;
      }
    },

    // Preprocess request
    useSessionPool: true,
    sessionPoolOptions: {
      maxPoolSize: 50,
      sessionOptions: {
        maxAgeSecs: 3000 // Rotate session every ~50 requests
      }
    }
  });

  // Add start URLs
  await crawler.addRequests(
    startUrls.map(url => ({
      url,
      userData: { depth: 0 }
    }))
  );

  // Run crawler
  await crawler.run();

  console.log('Scraping completed');

  // Get and log results
  const dataset = await Apify.openDataset('default');
  const info = await dataset.getInfo();
  console.log(`Total items scraped: ${info.itemCount}`);
});
```

---

## 7. キャッシング戦略

```typescript
// cache-manager.ts

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // milliseconds
  source: string;
}

class CacheManager {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private readonly maxCacheSize = 10000;

  set<T>(key: string, data: T, ttl: number, source: string): void {
    // LRU eviction if cache is full
    if (this.cache.size >= this.maxCacheSize) {
      const oldestKey = Array.from(this.cache.entries())
        .sort((a, b) => a[1].timestamp - b[1].timestamp)[0][0];
      this.cache.delete(oldestKey);
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
      source
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) return null;

    // Check expiry
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  invalidate(pattern: string): void {
    const regex = new RegExp(pattern);
    const keysToDelete: string[] = [];

    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.cache.delete(key));
  }

  clear(): void {
    this.cache.clear();
  }

  getStats(): {
    size: number;
    hitRate: number;
    totalHits: number;
    totalMisses: number;
  } {
    return {
      size: this.cache.size,
      hitRate: 0.75, // Example
      totalHits: 0,
      totalMisses: 0
    };
  }
}

// Usage
const cache = new CacheManager();

// Cache news articles for 5 minutes
cache.set(
  'news_search_ai',
  { articles: [...] },
  5 * 60 * 1000,
  'NewsData.io'
);

// Retrieve from cache
const cachedNews = cache.get('news_search_ai');
```

---

## 8. モニタリング・ログテンプレート

```typescript
// monitoring.ts

interface ApiMetrics {
  apiName: string;
  requestCount: number;
  successCount: number;
  failureCount: number;
  averageResponseTime: number;
  lastError?: string;
  lastErrorTime?: Date;
  uptime: number; // percentage
}

class ApiMonitor {
  private metrics: Map<string, ApiMetrics> = new Map();

  logRequest(apiName: string, success: boolean, responseTime: number, error?: Error): void {
    let metric = this.metrics.get(apiName);

    if (!metric) {
      metric = {
        apiName,
        requestCount: 0,
        successCount: 0,
        failureCount: 0,
        averageResponseTime: 0,
        uptime: 100
      };
      this.metrics.set(apiName, metric);
    }

    metric.requestCount++;
    if (success) {
      metric.successCount++;
    } else {
      metric.failureCount++;
      metric.lastError = error?.message;
      metric.lastErrorTime = new Date();
    }

    // Update average response time
    metric.averageResponseTime =
      (metric.averageResponseTime * (metric.requestCount - 1) + responseTime) /
      metric.requestCount;

    // Calculate uptime
    metric.uptime = (metric.successCount / metric.requestCount) * 100;

    // Alert if uptime drops
    if (metric.uptime < 95) {
      this.sendAlert(`${apiName} uptime dropped to ${metric.uptime.toFixed(2)}%`);
    }
  }

  getMetrics(apiName: string): ApiMetrics | undefined {
    return this.metrics.get(apiName);
  }

  getAllMetrics(): ApiMetrics[] {
    return Array.from(this.metrics.values());
  }

  private sendAlert(message: string): void {
    console.error(`ALERT: ${message}`);
    // Send to Slack, PagerDuty, etc.
  }
}

// Usage
const monitor = new ApiMonitor();

async function makeMonitoredApiCall(
  apiName: string,
  operation: () => Promise<any>
) {
  const startTime = Date.now();

  try {
    const result = await operation();
    const responseTime = Date.now() - startTime;
    monitor.logRequest(apiName, true, responseTime);
    return result;
  } catch (error: any) {
    const responseTime = Date.now() - startTime;
    monitor.logRequest(apiName, false, responseTime, error);
    throw error;
  }
}
```

---

このテンプレート集を使用することで、本番環境対応のAPIインテグレーションを効率的に構築できます。

