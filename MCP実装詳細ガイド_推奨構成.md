# MCP実装詳細ガイド - 推奨構成版

**対象**: 音声自動化システム Phase 1 実装
**実装期間**: 1週間
**難易度**: 低〜中

---

## Part 1: Firecrawl MCP セットアップ

### Step 1: APIキーの取得

```bash
# 1. Firecrawlアカウント作成
#    https://firecrawl.dev へアクセス
#    GitHubまたはメールで登録

# 2. APIキー取得
#    ダッシュボード → API Keys → Copy

# 3. 環境変数に保存
echo "FIRECRAWL_API_KEY=fc-your-key-here" >> ~/.zshenv
source ~/.zshenv
```

### Step 2: MCP統合

```json
// ~/.claude.json に追加
{
  "mcpServers": {
    "firecrawl": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "${FIRECRAWL_API_KEY}"
      },
      "disabled": false,
      "defer_loading": true,
      "search_keywords": ["scrape", "crawl", "web"],
      "category": "research",
      "cost_warning": true
    }
  }
}
```

### Step 3: テスト

```bash
# Claude Codeを再起動してテスト
# プロンプト例:
# "Firecrawlを使用してhttps://example.com の内容を抽出してください"

# JSONフォーマットで構造化データを抽出
# 日本語サイトでのテスト:
# "https://www.nikkei.com の最新ニュース記事を3件スクレイピングしてください"
```

---

## Part 2: YouTube Transcript MCP セットアップ

### Step 1: インストール

```bash
# npm経由でセットアップ
# ~/.claude.json に追加
{
  "youtube-transcript": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@fabriqa.ai/youtube-transcript-mcp"],
    "disabled": false,
    "defer_loading": true,
    "search_keywords": ["youtube", "transcript", "字幕", "動画"],
    "category": "media"
  }
}
```

### Step 2: 複数言語サポート設定

```javascript
// トランスクリプト取得の例
const getJapaneseTranscript = async (videoId) => {
  // 日本語トランスクリプト取得
  const result = await mcp.call('get-transcript', {
    videoId: videoId,
    language: 'ja'  // 日本語
  })

  return result
}

const getEnglishTranscript = async (videoId) => {
  // 英語トランスクリプト取得
  const result = await mcp.call('get-transcript', {
    videoId: videoId,
    language: 'en'
  })

  return result
}
```

### Step 3: 長動画対応

```javascript
// 25,000トークン制限への対応

// パターン1: タイムスタンプ削除
const getTranscriptWithoutTimestamps = async (videoId) => {
  const result = await mcp.call('get-transcript', {
    videoId: videoId,
    includeTimestamps: false  // サイズ20-30%削減
  })
  return result
}

// パターン2: チャンク処理
const processLongVideo = async (videoId) => {
  const languages = await mcp.call('get-transcript-languages', {
    videoId: videoId
  })

  // 利用可能な言語に対して逐次処理
  for (const lang of languages) {
    const transcript = await mcp.call('get-transcript', {
      videoId: videoId,
      language: lang.code
    })
    // 別々に処理
    await processTranscript(transcript)
  }
}
```

---

## Part 3: Local Voice MCP セットアップ

### Step 1: Python環境準備

```bash
# uvのインストール（Python パッケージマネージャー）
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Python 3.10+ の確認
python3 --version

# 推奨: Python 3.11または3.12
```

### Step 2: Voice MCP クローン・セットアップ

```bash
# リポジトリクローン
git clone https://github.com/jochiang/voice-mcp.git
cd voice-mcp

# 依存パッケージのインストール
uv pip install -r requirements.txt

# 初回実行（モデルダウンロード）
python main.py

# モデル自動ダウンロード場所:
# ~/.cache/huggingface/
# (~460MB + 260MB = 720MB)
```

### Step 3: GPU対応（オプション）

```bash
# NVIDIA GPU の場合（CUDA対応）
# cuDAが既にインストール済みの場合:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# macOS（M1/M3チップ）の場合:
# GPU非対応（Metal対応予定）
# CPUで問題なく動作
```

### Step 4: Claude Code統合

```json
{
  "voice-local": {
    "type": "stdio",
    "command": "python",
    "args": ["/path/to/voice-mcp/main.py"],
    "env": {
      "DEVICE": "cuda",  // または "cpu"
      "LANGUAGE": "ja",
      "TTS_MODEL": "kokoro"  // または "melotts"
    },
    "disabled": false,
    "defer_loading": true,
    "search_keywords": ["voice", "audio", "tts", "stt", "音声"],
    "category": "audio"
  }
}
```

### Step 5: テスト

```bash
# コマンドラインテスト
python main.py

# 日本語テキストの音声化:
# "これはテストです" → audio.wav

# 日本語音声の文字起こし:
# audio.wav → "これはテストです"
```

---

## Part 4: Pod Engine API MCP セットアップ

### Step 1: APIキー取得

```bash
# 1. Pod Engine登録
#    https://www.podengine.ai へアクセス

# 2. Developer Dashboard でAPIキー生成

# 3. 環境変数に保存
echo "POD_ENGINE_API_KEY=your-key-here" >> ~/.zshenv
source ~/.zshenv
```

### Step 2: MCP統合

```json
{
  "pod-engine": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "pod-engine-mcp"],
    "env": {
      "POD_ENGINE_API_KEY": "${POD_ENGINE_API_KEY}"
    },
    "disabled": false,
    "defer_loading": true,
    "search_keywords": ["podcast", "guest", "episodes", "ポッドキャスト"],
    "category": "media"
  }
}
```

### Step 3: API利用例

```javascript
// ポッドキャスト検索
const searchPodcasts = async (query) => {
  const result = await mcp.call('search-podcasts', {
    query: query,
    limit: 20
  })
  return result
}

// エピソード検索（トピック別）
const findEpisodesByTopic = async (topic) => {
  const result = await mcp.call('search-episodes', {
    query: topic,
    limit: 50
  })
  return result
}

// ゲスト検出
const findGuestsByName = async (name) => {
  const result = await mcp.call('search-guests', {
    name: name
  })
  return result
}
```

---

## Part 5: エンドツーエンド統合テスト

### テストシナリオ1: ニュース記事のポッドキャスト化

```bash
# 1. Firecrawlでニュースサイトをスクレイピング
# 2. テキスト要約（既存: mt5_summarize_japanese）
# 3. Local Voice MCPで音声化
# 4. Pod Engineでポッドキャストメタデータ取得
# 5. RSSフィード生成

プロンプト例:
"以下の流れでポッドキャストエピソードを自動生成してください:
1. https://www.nikkei.com の最新ニュースを3件スクレイピング
2. 各ニュースを日本語で200字に要約
3. 要約テキストを日本語ナレーション音声に変換
4. エピソード情報をPod Engineで取得
5. RSS フィードを生成"
```

### テストシナリオ2: YouTube動画のポッドキャスト化

```bash
# 1. YouTubeトランスクリプト取得
# 2. 長動画対応（タイムスタンプ削除）
# 3. 日本語文字起こし確認
# 4. テキスト要約
# 5. 音声化
# 6. RSS追加

プロンプト例:
"YouTubeビデオをポッドキャストに変換してください:
1. https://youtu.be/... からトランスクリプト取得
2. 日本語の要約生成
3. Local Voice MCPで音声化（女性の自然な声）
4. ポッドキャストメタデータ生成"
```

---

## Part 6: 監視・アラート設定

### Firecrawl APIの使用量監視

```bash
# .envに以下を追加
FIRECRAWL_API_KEY=your-key
FIRECRAWL_CREDIT_LIMIT=100  # 月額制限

# crontabで毎日チェック
0 9 * * * python check_firecrawl_credits.py

# check_firecrawl_credits.py の例:
import requests

def check_credits():
    headers = {"Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}"}
    response = requests.get("https://api.firecrawl.dev/v1/account", headers=headers)
    data = response.json()

    credits = data['credits_remaining']
    if credits < 10:
        send_alert(f"Firecrawl credits low: {credits}")
```

### ローカルストレージ監視（Local Voice）

```bash
# ~/.cache/huggingface/ の容量監視
0 9 * * * du -sh ~/.cache/huggingface/ | mail -s "Voice Cache" you@example.com

# 古いキャッシュの削除
find ~/.cache/huggingface/ -mtime +30 -delete
```

---

## Part 7: トラブルシューティング

### Firecrawl の一般的なエラー

```
エラー: "FIRECRAWL_API_KEY not found"
対策: 環境変数が正しく設定されているか確認
    source ~/.zshenv
    echo $FIRECRAWL_API_KEY

エラー: "Rate limit exceeded"
対策: 1分間のリクエスト数が多すぎる可能性
    - リトライロジックを追加
    - 指数バックオフを実装

エラー: "Japanese content not extracted properly"
対策: JSON形式で明示的なスキーマを指定
    - markdown形式では日本語がうまく抽出される
```

### YouTube Transcript の一般的なエラー

```
エラー: "No transcripts available"
対策: 手動字幕がない動画の場合
    - YouTubeの自動生成字幕を利用
    - 利用可能言語リストで確認してから取得

エラー: "Response exceeds 25,000 tokens"
対策: タイムスタンプを削除するか、動画をチャンク分割
    includeTimestamps: false
    // または複数のAPI呼び出しに分割
```

### Local Voice MCP の一般的なエラー

```
エラー: "CUDA out of memory"
対策: デバイスをCPUに変更するか、より小さいモデルを使用
    DEVICE=cpu python main.py
    TTS_MODEL=melotts  # Supertonic(260MB)より小さい

エラー: "モデルが自動ダウンロードされない"
対策: ネットワーク接続確認、キャッシュディレクトリの権限確認
    mkdir -p ~/.cache/huggingface/
    chmod 755 ~/.cache/huggingface/

エラー: "日本語の発音が不自然"
対策: 別のTTSモデルを試す
    - Kokoro（軽量、自然）
    - MeloTTS（高品質）
    - japanese-parler-tts-mini（制御可能）
```

---

## 推奨スケジュール

```
Week 1:
  Mon: Firecrawl セットアップ＆テスト
  Tue: YouTube Transcript セットアップ＆テスト
  Wed: Local Voice セットアップ＆テスト
  Thu: Pod Engine API セットアップ＆テスト
  Fri: 統合テスト＆ドキュメント

Week 2-3: 本番環境デプロイ
  - モニタリング設定
  - アラート設定
  - チーム教育
```

---

**最終更新**: 2026-02-11
