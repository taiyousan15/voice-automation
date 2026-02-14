# n8n Workflow 調査レポート: stand.fm自動化

**調査日**: 2026-02-14
**調査対象**: https://n8n.io/workflows/
**総ワークフロー数**: 8,305件
**調査結果**: stand.fm専用ワークフローは**存在しない**

---

## 調査結果サマリー

### stand.fm専用ワークフロー
**❌ 存在しない**

- n8n公式ライブラリ（8,305件）を検索
- "stand.fm"、"standfm"、"stand fm"で検索
- 該当ワークフローゼロ

### 関連ワークフロー（Podcast自動化）

| # | ワークフロー名 | URL | 用途 | stand.fm応用可能性 |
|---|--------------|-----|------|--------------------|
| 1 | **Upload podcast episodes to Spotify via RSS & Google Drive** | [リンク](https://n8n.io/workflows/7319-upload-podcast-episodes-to-spotify-via-rss-and-google-drive/) | MP3→Google Drive→RSS更新→Spotify配信 | ⭐⭐⭐（パターン参考可） |
| 2 | AI podcast generator with RSS feed & ElevenLabs voice | [リンク](https://n8n.io/workflows/5084-ai-podcast-generator-with-rss-feed-and-elevenlabs-voice/) | RSS→AI要約→音声生成 | ⭐⭐（音声生成参考） |
| 3 | Generate multispeaker podcast with AI | [リンク](https://n8n.io/workflows/2927-generate-multispeaker-podcast-with-ai-natural-sounding-and-google-sheets/) | Google Sheets→多話者音声→Drive保存 | ⭐⭐（台本→音声参考） |
| 4 | Convert Blog Posts to Podcast Episodes | [リンク](https://n8n.io/workflows/11897-convert-blog-posts-to-podcast-episodes-with-gpt-4o-elevenlabs-and-google-drive/) | ブログ→音声→Drive保存 | ⭐⭐（コンテンツ変換参考） |
| 5 | Convert RSS feeds into a podcast | [リンク](https://n8n.io/workflows/6945-convert-rss-feeds-into-a-podcast-with-google-gemini-kokoro-tts-and-ffmpeg/) | RSS→Gemini→Kokoro TTS→音声 | ⭐⭐⭐（TTS参考） |

---

## 最重要発見: Spotify自動アップロードワークフロー

### ワークフロー #7319 詳細

**名前**: Upload podcast episodes to Spotify via RSS & Google Drive
**作成者**: Luis Acosta (news2podcast.com)
**URL**: https://n8n.io/workflows/7319-upload-podcast-episodes-to-spotify-via-rss-and-google-drive/

#### 処理フロー

```
┌──────────────────────────────────────────────────────────┐
│ Step 1: MP3ファイル読み込み                               │
│   - ローカルパスまたは前段ワークフローから取得             │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────┐
│ Step 2: Google Driveにアップロード                        │
│   - 公開共有リンク生成                                    │
│   - 音声ファイルURLを取得                                 │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────┐
│ Step 3: GitHubからrss.xmlを取得                          │
│   - 既存のRSSフィードファイルをフェッチ                   │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────┐
│ Step 4: RSS <item>要素を追加                             │
│   - タイトル、説明、公開日を設定                         │
│   - MP3公開URLを<enclosure>に設定                        │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────┐
│ Step 5: 更新したrss.xmlをGitHubにコミット                │
│   - GitHubへプッシュ                                     │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────┐
│ Step 6: Spotify for Podcastersが自動で更新を検出         │
│   - RSSフィード監視で新エピソードを配信                  │
└──────────────────────────────────────────────────────────┘
```

#### 必要な認証情報

| サービス | 認証方法 | 必要な情報 |
|---------|---------|-----------|
| Google Drive | OAuth 2.0 | クライアントID、シークレット、フォルダID |
| GitHub | Personal Access Token | リポジトリ名、トークン |
| Spotify for Podcasters | RSS URL登録（初回のみ） | 事前にRSSをSpotifyに登録 |

#### 技術仕様

- **音声形式**: MP3（Spotify推奨）
- **RSS形式**: RSS 2.0準拠
- **enclosure必須**: `<enclosure url="..." type="audio/mpeg" length="..." />`
- **公開URL**: Google Driveの公開共有リンク

---

## stand.fmへの応用可能性

### パターン分析

Spotifyワークフローは以下のパターンを使用：

```
音声生成 → クラウドストレージ → RSS更新 → プラットフォーム自動検出
```

### stand.fmへの適用

**問題点**:
1. stand.fmは**RSS取り込み機能がない**（ディープリサーチで確認済み）
2. stand.fmは**公式APIがない**

**回避策（3つのアプローチ）**:

#### アプローチA: n8n + Playwright自動化

```
n8n Workflow:
  音声生成 → Google Drive保存
     ↓
  Playwrightノード（カスタムコード）
     ↓
  stand.fm Web版ログイン → アップロード → 投稿
```

**メリット**: 完全自動化可能
**デメリット**: Playwrightノードの実装が必要、規約違反リスク

#### アプローチB: n8n + Spotify/Apple Podcasts直接配信（推奨）

```
n8n Workflow:
  音声生成 → Google Drive保存 → GitHub RSS更新
     ↓
  Spotify/Apple Podcasts/Amazon Music自動配信
     ↓
  （stand.fmは手動アップロード）
```

**メリット**: 安全、公式機能のみ
**デメリット**: stand.fmは半自動

#### アプローチC: n8n + Transistor.fm MCP

```
n8n Workflow:
  音声生成
     ↓
  HTTP Request → Transistor.fm API
     ↓
  自動でRSS生成 → 各プラットフォーム配信
```

**メリット**: 完全自動、API公式対応
**デメリット**: $19/月のコスト

---

## 既存システムへの統合提案

### 現状のパイプライン

```
NewsData.io → Groq台本生成 → (VOICEVOX音声生成) → GitHub Pages RSS
```

### n8n統合パターン1: GitHub Actions → n8n連携

```
GitHub Actions:
  ニュース収集 → 台本生成 → 音声生成 → episodes/保存
     ↓ Webhook
n8n Workflow:
  MP3受信 → Google Drive保存 → GitHub RSS更新 → Spotify配信
```

**必要な変更**:
- GitHub ActionsにWebhookステップ追加
- n8n Webhookトリガー設定
- Google Drive認証設定

### n8n統合パターン2: 完全n8n化

```
n8n Workflow（全自動）:
  Schedule Trigger（毎日06:00 JST）
     ↓
  HTTP Request → NewsData.io API
     ↓
  HTTP Request → Groq API（台本生成）
     ↓
  HTTP Request → VOICEVOX API（音声生成）
     ↓
  Google Drive → MP3保存
     ↓
  GitHub → RSS更新
     ↓
  Spotify/Apple Podcasts自動配信
```

**メリット**: GitHub Actions不要、n8nで一元管理
**デメリット**: n8nサーバーが必要（セルフホストまたはクラウド）

---

## 実装推奨プラン

### Phase 1: 既存システム拡張（GitHub Actions + RSS直接配信）

**実装内容**:
1. `src/publishers/rss_generator.py`にMP3 enclosure追加
2. GitHub Pagesで音声ファイルホスティング
3. Spotify/Apple Podcastsに初回RSS登録

**メリット**: 既存資産活用、追加コストゼロ
**実装時間**: 2-3時間

### Phase 2: n8n Spotify連携（オプション）

**実装内容**:
1. n8nセルフホストまたはクラウド契約
2. ワークフロー #7319をインポート
3. GitHub Actions → n8n Webhook連携

**メリット**: n8nの可視化UI、エラーハンドリング強化
**実装時間**: 1日

### Phase 3: stand.fm Playwright自動化（リスク承知）

**実装内容**:
1. n8nにPlaywrightカスタムコードノード追加
2. stand.fm自動投稿フロー実装

**メリット**: stand.fmも完全自動化
**リスク**: 規約違反、アカウント停止の可能性
**実装時間**: 2-3日

---

## n8n料金

| プラン | 月額 | ワークフロー数 | 実行回数 |
|--------|------|--------------|---------|
| **Community（セルフホスト）** | 無料 | 無制限 | 無制限 |
| Starter | $20 | 無制限 | 5,000 |
| Pro | $50 | 無制限 | 10,000 |
| Enterprise | カスタム | 無制限 | 無制限 |

**推奨**: Community版をVPS（$5/月）でセルフホスト

---

## 出典

### n8n公式
- [n8n Workflows Library](https://n8n.io/workflows/) - 8,305ワークフロー
- [Upload podcast episodes to Spotify via RSS & Google Drive](https://n8n.io/workflows/7319-upload-podcast-episodes-to-spotify-via-rss-and-google-drive/)
- [AI podcast generator with RSS feed & ElevenLabs voice](https://n8n.io/workflows/5084-ai-podcast-generator-with-rss-feed-and-elevenlabs-voice/)
- [n8n Documentation](https://docs.n8n.io/)

### 技術記事
- [Yastime: Upload Podcast Episodes to Spotify](https://yastime.net/en/blogs/n8n-workflows/upload-podcast-episodes-to-spotify-via-rss-google-drive)
- [n8n GitHub](https://github.com/n8n-io/n8n)

### 関連ワークフロー
- [Generate multispeaker podcast](https://n8n.io/workflows/2927-generate-multispeaker-podcast-with-ai-natural-sounding-and-google-sheets/)
- [Convert Documents to Podcast Audio](https://n8n.io/workflows/6138-convert-documents-to-podcast-audio-with-gpt-4o-and-openai-tts/)
- [Automate podcast creation with GPT, Claude & Eleven Labs](https://n8n.io/workflows/10051-automate-podcast-creation-with-gpt-claude-and-eleven-labs-text-to-speech/)
- [Convert Blog Posts to Podcast Episodes](https://n8n.io/workflows/11897-convert-blog-posts-to-podcast-episodes-with-gpt-4o-elevenlabs-and-google-drive/)
- [Convert RSS feeds into a podcast](https://n8n.io/workflows/6945-convert-rss-feeds-into-a-podcast-with-google-gemini-kokoro-tts-and-ffmpeg/)

---

**結論**:
- stand.fm専用n8nワークフローは存在しない
- Spotify自動配信パターンが参考になる
- **推奨**: 既存GitHub ActionsでRSS直接配信（Spotify/Apple Podcasts）、stand.fmは手動補助
- **オプション**: n8n導入でワークフロー可視化とエラーハンドリング強化

**次のアクション**: Phase 1（RSS直接配信）を実装するか確認してください。
