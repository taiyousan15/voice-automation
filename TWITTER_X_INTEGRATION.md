# Twitter/X API統合ガイド

**作成日**: 2026-02-11
**ステータス**: ✅ セットアップ完了
**MCP**: twitter-client (agent-twitter-client-mcp)

---

## 📋 概要

ポッドキャスト自動化システムに Twitter/X 投稿機能を統合しました。Cookie認証方式で、以下の機能を提供します:

- ✅ エピソード自動投稿
- ✅ ハッシュタグ付き配信通知
- ✅ トレンド監視
- ✅ メンション対応（将来）

---

## 🔧 セットアップ手順

### Step 1: 認証情報の取得

Chrome DevToolsを使用して Twitter Cookie を取得してください:

#### 方法A: Chrome DevTools（推奨）

1. Twitter.com にログイン
2. F12 キーで DevTools を開く
3. **Application** タブ → **Cookies** → **https://x.com**
4. 以下の3つのCookieをコピー:
   - `auth_token` (約200文字)
   - `ct0` (32文字)
   - `twid` (数字、例: 123456789)

```
例:
auth_token=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...
ct0=abcdef1234567890abcdef1234567890
twid=1234567890
```

#### 方法B: curl を使用

```bash
# Cookie情報をファイルに保存
curl -c /tmp/twitter_cookies.txt \
  -d "username_or_email=your_email&password=your_password" \
  https://twitter.com/i/api/1.1/guest/activate.json

# 取得したCookieを確認
cat /tmp/twitter_cookies.txt | grep -E "auth_token|ct0|twid"
```

---

### Step 2: .env ファイル設定

プロジェクトディレクトリで `.env` ファイルを作成:

```bash
# .env.exampleからコピー
cp .env.example .env
```

`.env` ファイルを編集し、Twitter Cookie を設定:

```bash
# ===== SOCIAL MEDIA - Twitter/X =====
# Format: "auth_token=<value>;ct0=<value>;twid=<value>"
TWITTER_COOKIES=auth_token=YOUR_AUTH_TOKEN_HERE;ct0=YOUR_CT0_HERE;twid=YOUR_TWID_HERE
TWITTER_AUTO_POST_ENABLED=true
TWITTER_HASHTAGS=#ポッドキャスト #AI #自動化
TWITTER_POST_DELAY_SECONDS=10
```

**⚠️ セキュリティ警告**:
- `.env` ファイルを Git にコミット**しないでください**
- `.gitignore` に `.env` が含まれていることを確認してください
- Cookie情報は機密情報です。共有しないでください
- Cookie有効期限: 約3-6ヶ月（期限切れ時は再取得）

---

### Step 3: .mcp.json 確認

Twitter/X MCP は既に `.mcp.json` に設定済みです:

```json
{
  "twitter-client": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "agent-twitter-client-mcp"],
    "env": {
      "AUTH_METHOD": "cookies",
      "TWITTER_COOKIES": "${TWITTER_COOKIES}"
    },
    "disabled": false,
    "defer_loading": true,
    "search_keywords": ["twitter", "X", "ツイート", "SNS", "トレンド"],
    "description": "Twitter/X Client - ツイート検索・取得・投稿（Cookie認証）",
    "category": "sns-research"
  }
}
```

**確認項目**:
- ✅ `disabled: false` (有効)
- ✅ `AUTH_METHOD: "cookies"` (Cookie認証)
- ✅ `TWITTER_COOKIES` 環境変数参照

---

### Step 4: システム再起動

MCP設定を反映させるため、Claude Codeを再起動:

```bash
# Option A: Claude Codeアプリを再起動
# Cmd+Q で終了して再度起動

# Option B: MCP接続をリセット
# Claude Codeのコマンドパレット (Cmd+Shift+P) で:
# "MCP: Restart Server" を選択
```

---

## ✅ 動作確認

### テストコマンド

```bash
# 1. MCP接続確認
mcp list-resources twitter-client

# 2. ツイート検索テスト
mcp search-tweets -q "podcast" -count=5

# 3. 投稿テスト（ドライラン）
mcp post-tweet \
  --text="🎧 テストツイート\n\nこれはテスト投稿です。\n\n#ポッドキャスト #AI" \
  --dry-run=true
```

### Claude Code内テスト

```
ユーザー: "Twitterに『🎧 ポッドキャスト自動化システムのテストツイートです #AI』と投稿してください"
```

期待される動作:
- Twitter APIへの接続確認
- ツイート文のバリデーション
- 投稿実行（自動）

---

## 📊 投稿テンプレート

エピソード自動投稿時のテンプレート:

```
[EPISODE] {episode_title}

🎧 {episode_description}

📻 Podcast: {episode_duration}分

▶️ Listen: {feed_url}

#ポッドキャスト #AI #自動化
```

**カスタマイズ例**:

```env
TWITTER_HASHTAGS=#テックニュース #AI #ポッドキャスト #自動化
TWITTER_TEMPLATE=[🎙️ NEW] {title}\n\n{description}\n\nListen: {url}\n\n{hashtags}
TWITTER_INCLUDE_AUDIO=true  # 音声ファイルをツイートに添付
TWITTER_INCLUDE_IMAGE=true  # サムネイルをツイートに添付
```

---

## 🔄 フォールバック戦略

Twitter APIが利用不可の場合:

1. **第1段階** (優先度: 高)
   - `twitter-client` MCP 経由で投稿
   - Cookie認証使用
   - 再試行回数: 3回

2. **第2段階** (優先度: 中)
   - open-websearch MCP 経由で X検索
   - トレンド情報取得のみ
   - 投稿不可

3. **第3段階** (優先度: 低)
   - ローカルログに記録
   - 手動投稿キューに追加
   - 後で復帰時に送信

---

## 🚨 トラブルシューティング

### エラー: "TWITTER_COOKIES not found"

**原因**: `.env` ファイルが設定されていない

**対処**:
```bash
# .env ファイルの作成確認
ls -la .env

# ファイルが없으면 作成
cp .env.example .env
nano .env  # 編集
```

### エラー: "Invalid auth_token format"

**原因**: Cookie形式が正しくない

**確認**:
```bash
# Cookie形式が正しいか確認
grep TWITTER_COOKIES .env
# 出力例: TWITTER_COOKIES=auth_token=xxx;ct0=yyy;twid=zzz
```

### エラー: "401 Unauthorized"

**原因**: Cookie有効期限切れ

**対処**:
1. Chrome DevTools で新しい Cookie を取得
2. `.env` ファイルを更新
3. Claude Code を再起動

### エラー: "Rate limit exceeded"

**原因**: Twitter API レート制限に引っかかった

**対処**:
```env
# 投稿間隔を増加
TWITTER_POST_DELAY_SECONDS=30  # デフォルト: 10秒
TWITTER_MAX_POSTS_PER_HOUR=300  # 制限設定
```

---

## 📈 統計・ダッシュボード

Twitter投稿の統計情報:

```sql
SELECT
  DATE(created_at) as date,
  COUNT(*) as total_posts,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_posts,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_posts,
  ROUND(AVG(likes_count), 2) as avg_likes,
  ROUND(AVG(retweets_count), 2) as avg_retweets
FROM twitter_posts
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

Grafana ダッシュボード:
- ツイート投稿数 (日次)
- エンゲージメント率 (いいね/リツイート)
- エラー率
- API レート制限状況

---

## 🔐 セキュリティ注意事項

### Cookie 認証の安全性

✅ **安全な使用方法**:
- Cookie は環境変数で管理
- `.env` を `.gitignore` に含める
- CI/CD パイプラインでは secrets を使用
- 定期的に Cookie を更新（6ヶ月ごと）

❌ **危険な使用方法**:
- Cookie をコードに埋め込む
- Cookie を Slack や Email で共有
- Cookie を Git リポジトリにコミット

### 監査ログ

すべての Twitter 操作はログに記録されます:

```
2026-02-11 06:00:15 [TWITTER] POST successful - tweet_id=12345678
2026-02-11 06:01:02 [TWITTER] POST failed - error="rate_limit"
2026-02-11 06:05:30 [TWITTER] SEARCH completed - 10 results
```

ログ保持期間: **30日間**

---

## 🔗 関連ドキュメント

- `.env.example` - 環境変数テンプレート
- `.mcp.json` - MCP設定ファイル
- `チームキックオフ資料.md` - プロジェクト全体計画
- `技術スタック検証レポート.md` - 技術仕様書

---

## 📞 サポート

### よくある質問

**Q: 複数の Twitter アカウントで投稿できる？**
A: はい。複数の TWITTER_COOKIES を環境変数で管理し、TWITTER_ACCOUNT_ID で切り替え可能です。

**Q: ツイートをスケジュール投稿できる？**
A: いいえ。リアルタイム投稿のみです。スケジュール投稿は Twitter Pro ($5/月) で利用可能です。

**Q: リプライやメンション対応は？**
A: Phase 2 で実装予定です。現在はエピソード通知投稿のみ。

**Q: 画像やメディアを含められる？**
A: はい。TWITTER_INCLUDE_IMAGE=true で自動的にサムネイルを添付します。

---

## ✨ 次のステップ

1. ✅ **今すぐ**: `.env` ファイル設定
2. ✅ **今すぐ**: MCP テスト実行
3. 📅 **Week 2**: エピソード自動投稿テスト
4. 📅 **Week 3**: 本番環境への展開
5. 📅 **Week 4**: Analytics ダッシュボード構築

---

**最後更新**: 2026-02-11
**MCP Version**: agent-twitter-client-mcp 1.0+
**ステータス**: ✅ 統合完了・セットアップ待ち
