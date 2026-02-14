# GitHub Pages セットアップガイド

## 概要

このガイドでは、ポッドキャスト自動化システムをGitHub Pagesで公開する手順を説明します。

---

## 前提条件

- GitHubリポジトリが作成されていること
- GitHub Actionsが有効化されていること
- 以下のSecretsが設定されていること

---

## 必須Secrets設定

GitHubリポジトリの **Settings → Secrets and variables → Actions** で以下を設定:

| Secret名 | 説明 | 取得方法 |
|---------|------|----------|
| `GROQ_API_KEY` | Groq API Key | https://console.groq.com/keys |
| `NEWSDATA_API_KEY` | NewsData.io API Key | https://newsdata.io/dashboard |
| `OPENROUTER_API_KEY` | OpenRouter API Key | https://openrouter.ai/keys |
| `ANTHROPIC_API_KEY` | Anthropic API Key | https://console.anthropic.com/ |
| `FISH_AUDIO_API_KEY` | Fish Audio API Key | https://fish.audio/dashboard |
| `FISH_AUDIO_VOICE_ID` | Fish Audio Voice ID | Fish Audioダッシュボードから取得 |
| `VOICEVOX_API_URL` | VOICEVOX API URL（オプション） | ローカルまたはリモートVOICEVOXサーバー |

---

## GitHub Pages有効化手順

### 1. リポジトリ設定

1. GitHubリポジトリの **Settings** に移動
2. 左メニューから **Pages** を選択
3. **Source** で以下を設定:
   - Source: **Deploy from a branch**
   - Branch: **gh-pages** / **/ (root)**
4. **Save** をクリック

### 2. GitHub Actions実行

#### 手動実行（初回テスト推奨）

1. リポジトリの **Actions** タブに移動
2. **Podcast Automation Pipeline** ワークフローを選択
3. **Run workflow** → **Run workflow** をクリック
4. 実行完了を待つ（約5-10分）

#### 自動実行（本番運用）

- **毎日06:00 JST**（21:00 UTC前日）に自動実行
- GitHub Actionsのcronスケジュールで設定済み

---

## 公開URL

ワークフロー実行成功後、以下のURLでアクセス可能:

```
https://<USERNAME>.github.io/<REPO_NAME>/
```

例: `https://yourusername.github.io/podcast-automation/`

### エンドポイント

| エンドポイント | 説明 |
|--------------|------|
| `/` | ランディングページ（エピソード一覧） |
| `/feed.xml` | RSS 2.0 フィード（ポッドキャストアプリ用） |
| `/summary.json` | エピソードメタデータ（API用） |

---

## RSS Feedの使い方

### ポッドキャストアプリへの登録

1. 公開URLの `/feed.xml` をコピー
   ```
   https://<USERNAME>.github.io/<REPO_NAME>/feed.xml
   ```

2. 対応ポッドキャストアプリで登録:
   - **Apple Podcasts**: 「ライブラリ」→「フィードURLで番組を追加」
   - **Google Podcasts**: 検索→「RSSフィードから登録」
   - **Spotify**: スマホアプリから直接登録不可（RSS取り込み機能を使用）
   - **stand.fm**: RSS取り込み機能を使用
   - **その他**: 大半のポッドキャストアプリでRSS URL登録対応

---

## トラブルシューティング

### GitHub Pages が表示されない

**原因**: gh-pagesブランチが作成されていない

**解決策**:
1. Actions タブで最新のワークフロー実行を確認
2. "Deploy to GitHub Pages" ステップが成功しているか確認
3. 失敗している場合はログを確認し、Secretsが正しく設定されているか確認

### RSS Feedが更新されない

**原因**: ワークフローが実行されていない

**解決策**:
1. Actions タブで最新の実行を確認
2. 手動で "Run workflow" を実行してテスト
3. cron設定を確認（`.github/workflows/podcast-automation.yml` の `schedule` セクション）

### 音声生成に失敗する

**原因**: API Keyが無効 or タイムアウト

**解決策**:
1. API Keyを再確認
2. ダッシュボードで残クレジットを確認
3. `.env` ファイルでタイムアウト設定を確認

### テーマが反映されない

**原因**: `config.yaml` の設定が読み込まれていない

**解決策**:
1. `config.yaml` が正しくコミットされているか確認
2. themes配列に必要なテーマが含まれているか確認
3. keyword_expansion.enabled が true になっているか確認

---

## ローカルテスト

GitHub Actionsにプッシュする前にローカルでテスト:

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# .envファイル設定
cp .env.example .env
# .envを編集してAPI Keyを設定

# パイプライン実行
python3 -m src.orchestrator --enable-audio

# 生成されたファイル確認
ls -lh episodes/
```

---

## 運用ベストプラクティス

### 1. クレジット管理

- **Groq**: 無料プラン 7,000リクエスト/日 → 月額$0.59/M tokensで十分
- **NewsData.io**: 無料プラン 200リクエスト/日 → 商用利用可能
- **Anthropic**: Haiku $1/$5 per 1M tokens → keyword拡張で月額~¥340

### 2. エラー通知

GitHub Actionsの失敗通知を有効化:
1. リポジトリの **Settings → Notifications** で設定
2. Actions失敗時にメール通知を受け取る

### 3. バックアップ

Artifacts（成果物）は30日間保存:
- `podcast-outputs-{run_id}`: 全エピソードファイル
- `rss-feed-{run_id}`: RSS Feed

必要に応じてローカルにダウンロード:
```bash
gh run download <run_id>
```

---

## 次のステップ

- [ ] GitHub PagesでRSS Feedが正しく配信されることを確認
- [ ] ポッドキャストアプリでRSS登録テスト
- [ ] 自動実行スケジュールの調整（必要に応じて）
- [ ] テーマ・キーワードのカスタマイズ（`config.yaml`）
- [ ] 音声品質の最適化（Voice IDの変更）
