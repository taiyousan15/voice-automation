# デプロイメント実装ガイド

**最終更新**: 2026-02-14
**ステータス**: Phase 1完了 - 本番デプロイ準備完了

---

## 概要

このガイドでは、ポッドキャスト自動配信システムを本番環境にデプロイする手順を説明します。

**現在の実装状態**:
- ✅ ニュース収集（NewsData.io）
- ✅ 台本生成（Groq LLM）
- ✅ RSS 2.0フィード生成（iTunes/Spotify対応）
- ✅ GitHub Actions自動実行（毎日06:00 JST）
- ✅ GitHub Pagesデプロイ
- ⏳ 音声生成（VOICEVOX API設定後に有効化）

---

## デプロイ前チェックリスト

### 1. 必須API キー

以下のAPIキーを取得済みであることを確認：

| API | 状態 | 取得先 |
|-----|------|--------|
| GROQ_API_KEY | ✅ | https://console.groq.com/ |
| NEWSDATA_API_KEY | ✅ | https://newsdata.io/ |
| OPENROUTER_API_KEY | ✅ | https://openrouter.ai/ |
| VOICEVOX_API_URL | ⏳ | 後述 |

### 2. GitHubリポジトリ設定

- ✅ リポジトリ作成済み: `https://github.com/taiyousan15/voice-automation`
- ✅ GitHub Pages有効化
- ✅ GitHub Actions有効化

---

## デプロイ手順

### Step 1: GitHub Secrets設定

リポジトリの Settings → Secrets and variables → Actions で以下を登録：

```bash
# 必須（既に設定済み）
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NEWSDATA_API_KEY=pub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxx

# オプション（VOICEVOX使用時のみ）
VOICEVOX_API_URL=https://your-voicevox-api.example.com
```

**確認方法**:
1. https://github.com/taiyousan15/voice-automation/settings/secrets/actions
2. 上記3つのSecretsが登録されていることを確認

---

### Step 2: 初回手動実行

GitHub Actionsを手動トリガーで実行し、動作確認：

1. **Actionsタブへ移動**
   ```
   https://github.com/taiyousan15/voice-automation/actions
   ```

2. **ワークフローを選択**
   - "Podcast Automation Pipeline" をクリック

3. **手動実行**
   - "Run workflow" ボタンをクリック
   - "Run workflow" を再度クリックして確認

4. **実行結果確認**
   - 実行時間: 約30-60秒
   - 緑のチェックマーク ✅ = 成功

---

### Step 3: 生成されたRSSフィードの確認

GitHub Pagesにデプロイされたコンテンツを確認：

**RSS Feed URL**:
```
https://taiyousan15.github.io/voice-automation/podcast/feed.xml
```

**確認項目**:
- [ ] HTTP 200 で正常にアクセスできる
- [ ] XMLが正しく表示される
- [ ] エピソードが含まれている（`<item>` タグ）
- [ ] 日本語が正しく表示される

**ブラウザで確認**:
```bash
# curlで確認
curl -I https://taiyousan15.github.io/voice-automation/podcast/feed.xml

# 期待される出力
HTTP/2 200
content-type: application/xml
```

---

### Step 4: プラットフォーム登録（初回のみ）

詳細は `docs/PLATFORM_REGISTRATION.md` を参照。

#### 推奨プラットフォーム

1. **Apple Podcasts** ⭐⭐⭐⭐⭐
   - URL: https://podcastsconnect.apple.com/
   - 審査期間: 1-3日

2. **Spotify for Podcasters** ⭐⭐⭐⭐⭐
   - URL: https://podcasters.spotify.com/
   - 審査期間: 即時

3. **Amazon Music for Podcasters** ⭐⭐⭐⭐
   - URL: https://podcasters.amazon.com/
   - 審査期間: 1-2日

**登録手順（共通）**:
1. プラットフォームにログイン
2. "新しいポッドキャストを追加"
3. RSS URL を入力: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`
4. 審査待ち

**登録後の動作**:
- 毎日06:00 JSTに新エピソードが自動生成される
- プラットフォームが1-24時間以内に新エピソードを検出
- 自動的にリスナーに配信される

---

## 音声生成の有効化（オプション）

現在、パイプラインは**音声なし**で動作しています。音声生成を有効化するには、VOICEVOX APIエンドポイントが必要です。

### オプション1: Google Colab（推奨）

1. **Google Colabでセットアップ**
   ```python
   # scripts/test_voicevox.py の手順に従う
   !pip install voicevox-core
   # VOICEVOX Nemo APIサーバーを起動
   ```

2. **ngrokでトンネル作成**
   ```bash
   !ngrok http 50021
   # 公開URL（例: https://xxxxx.ngrok.io）をコピー
   ```

3. **GitHub Secretsに登録**
   ```
   VOICEVOX_API_URL=https://xxxxx.ngrok.io
   ```

**注意**: ngrokの無料プランは8時間でセッション切れるため、本番運用には不向き

---

### オプション2: VPSデプロイ（本番推奨）

1. **VPSを用意**（推奨: DigitalOcean, Linode, AWS Lightsail）
   - スペック: 2GB RAM以上、10GB ストレージ
   - OS: Ubuntu 22.04

2. **VOICEVOX Nemo Dockerをデプロイ**
   ```bash
   # VPSにSSH接続
   ssh user@your-vps-ip

   # Dockerインストール
   curl -fsSL https://get.docker.com | sh

   # VOICEVOX Nemo起動
   docker run -d -p 50021:50021 \
     --name voicevox \
     --restart unless-stopped \
     voicevox/voicevox_engine:cpu
   ```

3. **ファイアウォール設定**
   ```bash
   sudo ufw allow 50021/tcp
   ```

4. **GitHub Secretsに登録**
   ```
   VOICEVOX_API_URL=http://your-vps-ip:50021
   ```

5. **動作確認**
   ```bash
   curl http://your-vps-ip:50021/speakers
   # スピーカー一覧が返ってくればOK
   ```

---

### オプション3: 音声生成スキップ（現在の設定）

VOICEVOX_API_URLが未設定の場合、音声生成は自動的にスキップされ、テキストのみのRSSフィードが生成されます。

**メリット**:
- コスト不要
- セットアップ不要
- テキストベースのポッドキャストとして機能

**デメリット**:
- 音声ファイルが生成されない
- プラットフォームによっては音声必須の場合がある

---

## 運用監視

### 1. GitHub Actions実行履歴

定期実行（毎日06:00 JST）が正常に動作しているか確認：

```
https://github.com/taiyousan15/voice-automation/actions
```

**確認項目**:
- [ ] 毎日実行されている
- [ ] 実行時間が10分以内
- [ ] 緑のチェックマーク ✅ が表示される

---

### 2. RSS Feed更新確認

RSSフィードが最新のエピソードを含んでいるか確認：

```bash
curl https://taiyousan15.github.io/voice-automation/podcast/feed.xml | grep "<pubDate>"
```

**期待される出力**:
```xml
<pubDate>2026-02-14T06:00:00+09:00</pubDate>
```

---

### 3. エラー通知（オプション）

GitHub Actionsが失敗した場合の通知を設定：

1. **GitHubのNotifications設定**
   - Settings → Notifications → Actions
   - "Send notifications for failed workflows only" を有効化

2. **Emailで通知**
   - 自動的にGitHubアカウントのメールアドレスに通知される

---

## トラブルシューティング

### 問題1: GitHub Actionsが失敗する

**症状**: ワークフローが赤い✗マークで失敗

**確認手順**:
1. ログを確認: `https://github.com/taiyousan15/voice-automation/actions`
2. エラーメッセージを読む

**よくあるエラー**:

#### API Key not found
```
KeyError: 'GROQ_API_KEY'
```

**解決策**: GitHub Secretsに正しいAPI Keyを登録

#### Rate Limit Exceeded
```
NewsData.io API rate limit exceeded
```

**解決策**: 24時間待つ、または有料プランにアップグレード

---

### 問題2: RSSフィードが更新されない

**症状**: 新しいエピソードが表示されない

**確認手順**:
1. GitHub Actionsが成功しているか確認
2. GitHub Pagesのデプロイが完了しているか確認（gh-pagesブランチ）

**解決策**:
```bash
# gh-pagesブランチを確認
git fetch origin gh-pages
git log origin/gh-pages -1

# 最新のコミットが今日の日付であることを確認
```

---

### 問題3: 音声生成が失敗する

**症状**: `✗ Audio generation failed`

**確認手順**:
1. VOICEVOX_API_URLが正しく設定されているか
2. VOICEVOX APIサーバーが起動しているか

**解決策**:
```bash
# VOICEVOX API接続確認
curl ${VOICEVOX_API_URL}/speakers

# 正常なレスポンス例
[{"name":"四国めたん","styles":[{"name":"ノーマル","id":0}]}]
```

---

## 次のステップ

### Phase 1完了後（現在）

- ✅ RSS配信が自動化されている
- ✅ プラットフォーム登録可能
- ⏳ 音声生成（VOICEVOX設定後）

### Phase 2: stand.fm自動化（オプション）

詳細は `research/stand_fm_deep_research.md` を参照。

**注意**: stand.fmには公式APIが存在しないため、Playwright自動化はリスクあり。

### Phase 3: n8nワークフロー可視化（オプション）

詳細は `research/n8n_workflow_research.md` を参照。

---

## サポート

### ドキュメント

- **プラットフォーム登録**: `docs/PLATFORM_REGISTRATION.md`
- **セッション引継ぎ**: `SESSION_HANDOFF.md`
- **技術仕様**: `work_logs/2026-02-14_PHASE1_PROGRESS.md`

### リサーチレポート

- **stand.fm調査**: `research/stand_fm_deep_research.md`
- **n8nワークフロー**: `research/n8n_workflow_research.md`

---

**最終更新**: 2026-02-14T03:00:00+09:00
**担当**: Claude Sonnet 4.5
**ステータス**: デプロイ準備完了 ✅
