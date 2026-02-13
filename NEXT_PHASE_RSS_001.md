# RSS-001: GitHub Pages デプロイと RSS 配信

**Status**: Ready for Implementation
**Depends On**: GH-ACTIONS-001 ✅ (COMPLETED in 051ef23)
**Target**: Week 2, Day 2 - GitHub Pages hosting and RSS distribution

---

## 概要

GH-ACTIONS-001で生成されたRSSフィードを、GitHub Pagesで公開して、stand.fmやnote.comから参照できるようにします。

### 目的
- RSS フィードを公開URLで配信
- GitHub Pages ホスティング設定
- stand.fm RSS取り込み設定
- note.com 記事テンプレート生成

---

## 実装スコープ

### 1. GitHub Pages 有効化
**リポジトリ設定**: Settings → Pages

```yaml
# GitHub Pages設定
Source: GitHub Actions
Branch: main
Path: /docs (または /episodes)
```

### 2. GitHub Actions ワークフロー更新
**ファイル**: `.github/workflows/podcast-automation.yml`

以下のステップを追加：
```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./episodes
    destination_dir: podcast
    keep_files: false
```

### 3. RSS フィードURL
公開後のRSS URL:
```
https://taiyousan15.github.io/voice-automation/podcast/feed.xml
```

### 4. stand.fm RSS取り込み設定
1. stand.fm にログイン
2. 設定 → RSS取り込み
3. RSS URL を入力: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`
4. 取り込み間隔: 毎日

### 5. note.com 記事テンプレート生成
**ファイル**: `src/publishers/note_template.py`

```python
def generate_note_template(episode_data: dict) -> str:
    """
    note.com用の記事テンプレートを生成

    Args:
        episode_data: エピソードデータ（台本、メタデータ）

    Returns:
        note.com記事テンプレート（Markdown形式）
    """
    template = f"""
# {episode_data['title']}

> 📻 **ポッドキャスト配信中**
> [stand.fmで聴く](https://stand.fm/episodes/...)

## 本日のトピック

{episode_data['summary']}

## 記事一覧

{format_articles(episode_data['articles'])}

---

**📡 RSSフィード**: [購読する](https://taiyousan15.github.io/voice-automation/podcast/feed.xml)
"""
    return template
```

---

## 実装ステップ

### Phase 1: GitHub Pages 有効化（5分）
1. リポジトリ設定を開く: https://github.com/taiyousan15/voice-automation/settings/pages
2. Source: **GitHub Actions** を選択
3. 保存

### Phase 2: ワークフロー更新（10分）
1. `.github/workflows/podcast-automation.yml` を編集
2. GitHub Pages デプロイステップを追加
3. コミット＆プッシュ

### Phase 3: テスト実行（5分）
1. Manual trigger で実行
2. GitHub Pages デプロイ確認
3. RSS URL にアクセス: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`

### Phase 4: stand.fm 連携（10分）
1. stand.fm にログイン
2. RSS URL を登録
3. 取り込みテスト

### Phase 5: note.com テンプレート生成（15分）
1. `src/publishers/note_template.py` を実装
2. テストスクリプト作成
3. 実行確認

---

## 期待される成果物

### ✅ 公開RSS URL
```
https://taiyousan15.github.io/voice-automation/podcast/feed.xml
```

### ✅ GitHub Pages デプロイ
- episodes/ ディレクトリが公開される
- feed.xml がアクセス可能
- エピソード台本も公開（オプション）

### ✅ stand.fm 連携
- RSS取り込みで自動配信
- 毎日 06:00 JST に新エピソード配信

### ✅ note.com テンプレート
- Markdown形式の記事テンプレート
- 台本サマリー＋記事リンク
- RSSフィード購読リンク

---

## テスト方法

### 1. GitHub Pages デプロイ確認
```bash
# RSS フィードにアクセス
curl -I https://taiyousan15.github.io/voice-automation/podcast/feed.xml

# Expected:
# HTTP/2 200
# content-type: application/xml
```

### 2. RSS バリデーション
https://validator.w3.org/feed/ で検証

### 3. stand.fm テスト
- RSS取り込み後、stand.fmにエピソードが表示されるか確認

---

## トラブルシューティング

### GitHub Pages が 404 エラー
1. Settings → Pages で設定確認
2. GitHub Actions ワークフロー実行ログ確認
3. `publish_dir` のパスが正しいか確認

### stand.fm RSS取り込み失敗
1. RSS URLが正しいか確認
2. RSS 2.0 形式に準拠しているか確認
3. エンコーディングがUTF-8か確認

### note.com テンプレート生成エラー
1. episode_data の形式確認
2. Markdown エスケープ処理確認
3. URL形式確認

---

## 次のフェーズ向け

### INTEGRATION-001（Week 2, Day 3-4）
- VOICEVOX Nemo 音声生成統合
- TTS → MP3 変換
- MP3 → RSS enclosure 追加
- stand.fm 音声配信テスト

---

## PC再起動後の再開手順

1. **ローカル環境確認**
   ```bash
   cd /Users/matsumototoshihiko/Desktop/開発2026/音声自動化システム
   git status  # 051ef23 commit確認
   ```

2. **GitHub Pages 設定**
   - リポジトリ設定を開く
   - GitHub Actions を選択
   - テスト実行

3. **RSS URL 確認**
   - `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`
   - アクセス可能か確認

---

**作成日**: 2026-02-14
**Status**: Ready for Implementation
**Estimated Effort**: 45-60 minutes
