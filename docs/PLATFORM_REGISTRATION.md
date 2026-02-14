# プラットフォーム登録手順書

**最終更新**: 2026-02-14
**RSS Feed URL**: https://taiyousan15.github.io/voice-automation/podcast/feed.xml

---

## 概要

このドキュメントでは、自動生成されたポッドキャストを各プラットフォームに配信するための初回登録手順を説明します。

**重要**: 各プラットフォームへの登録は**初回のみ手動**で行います。登録後は、RSSフィードが自動的に更新されるため、新しいエピソードは自動配信されます。

---

## 配信可能なプラットフォーム

| プラットフォーム | 自動配信 | 料金 | 審査期間 | 推奨度 |
|----------------|---------|------|---------|--------|
| **Apple Podcasts** | ✅ | 無料 | 1-3日 | ⭐⭐⭐⭐⭐ |
| **Spotify** | ✅ | 無料 | 即時 | ⭐⭐⭐⭐⭐ |
| **Amazon Music** | ✅ | 無料 | 1-2日 | ⭐⭐⭐⭐ |
| **Google Podcasts** | ✅ | 無料 | 即時 | ⭐⭐⭐⭐ |
| **YouTube Podcasts** | ✅ | 無料 | 1-3日 | ⭐⭐⭐⭐ |
| **stand.fm** | ❌ 手動 | 無料 | - | ⭐⭐⭐ |
| **note.com** | ❌ 半自動 | 無料 | - | ⭐⭐ |

---

## 1. Apple Podcasts（推奨）

### 必要なもの
- Apple ID（無料）
- ポッドキャストカバーアート（1400x1400px以上、JPG/PNG）

### 登録手順

1. **Apple Podcasts Connect にアクセス**
   - URL: https://podcastsconnect.apple.com/
   - Apple ID でログイン

2. **新しいポッドキャストを追加**
   - 「+」ボタンをクリック
   - RSS Feed URL を入力: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`
   - 「Validate」をクリック

3. **ポッドキャスト情報を入力**
   - タイトル: `ポッドキャスト自動配信`
   - カテゴリ: `Technology`（または適切なカテゴリ）
   - 言語: `日本語`
   - 説明: `AI自動生成のポッドキャストエピソード`
   - カバーアート: アップロード（1400x1400px以上）

4. **所有権の確認**
   - 確認方法を選択（Email推奨）
   - 確認リンクをクリック

5. **審査待ち**
   - 通常1-3日で審査完了
   - 承認されたらApple Podcastsで配信開始

### トラブルシューティング

**エラー: "RSS feed is invalid"**
- 原因: MP3ファイルがまだ生成されていない
- 解決: Phase 1の音声生成を完了してから再試行

**エラー: "Artwork dimensions are too small"**
- 原因: カバーアートが1400x1400px未満
- 解決: 1400x1400px以上の画像を用意

---

## 2. Spotify for Podcasters（推奨）

### 必要なもの
- Spotifyアカウント（無料）
- ポッドキャストカバーアート（3000x3000px推奨、JPG/PNG）

### 登録手順

1. **Spotify for Podcasters にアクセス**
   - URL: https://podcasters.spotify.com/
   - Spotifyアカウントでログイン

2. **新しいポッドキャストを開始**
   - 「Get started」をクリック
   - 「Use an RSS feed」を選択

3. **RSS Feed URL を入力**
   - RSS URL: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`
   - 「Next」をクリック

4. **ポッドキャスト情報を確認**
   - RSSフィードから自動的に情報が取得される
   - 必要に応じて編集
   - カバーアート: 3000x3000px推奨

5. **公開**
   - 「Submit」をクリック
   - 即座にSpotifyで配信開始（審査なし）

### トラブルシューティング

**エラー: "RSS feed not found"**
- 原因: GitHub Pagesのデプロイが完了していない
- 解決: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml` にアクセスして確認

---

## 3. Amazon Music for Podcasters

### 必要なもの
- Amazonアカウント（無料）
- ポッドキャストカバーアート（3000x3000px推奨、JPG/PNG）

### 登録手順

1. **Amazon Music for Podcasters にアクセス**
   - URL: https://podcasters.amazon.com/
   - Amazonアカウントでログイン

2. **新しいポッドキャストを追加**
   - 「Add a podcast」をクリック
   - RSS Feed URL を入力: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`

3. **ポッドキャスト情報を確認**
   - 自動的に取得された情報を確認
   - カテゴリ、説明などを編集

4. **審査待ち**
   - 通常1-2日で審査完了
   - 承認されたらAmazon Musicで配信開始

---

## 4. Google Podcasts Manager

### 必要なもの
- Googleアカウント（無料）

### 登録手順

1. **Google Podcasts Manager にアクセス**
   - URL: https://podcastsmanager.google.com/
   - Googleアカウントでログイン

2. **RSS Feed URL を追加**
   - RSS URL: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`
   - 「Add feed」をクリック

3. **所有権の確認**
   - Googleの指示に従って所有権を確認
   - 確認後、即座に配信開始

---

## 5. YouTube Podcasts

### 必要なもの
- YouTubeチャンネル（無料）
- ポッドキャストカバーアート（1400x1400px以上、JPG/PNG）

### 登録手順

1. **YouTube Studio にアクセス**
   - URL: https://studio.youtube.com/
   - YouTubeアカウントでログイン

2. **Podcasts セクションへ移動**
   - 左メニューから「Podcasts」を選択
   - 「Add podcast」をクリック

3. **RSS Feed URL を入力**
   - RSS URL: `https://taiyousan15.github.io/voice-automation/podcast/feed.xml`
   - 「Next」をクリック

4. **審査待ち**
   - 通常1-3日で審査完了
   - 承認されたらYouTubeで配信開始

---

## 6. stand.fm（手動アップロード）

### 背景

**重要**: stand.fmには以下の制限があります:
- ✅ **RSS配信機能あり**（stand.fm → 外部への配信）
- ❌ **RSS取り込み機能なし**（外部 → stand.fmへの配信は不可）
- ❌ **公式API なし**

したがって、stand.fmへの配信は**手動アップロード**または**Playwright自動化**（規約リスクあり）が必要です。

### 手動アップロード手順

1. **stand.fm にログイン**
   - URL: https://stand.fm/
   - アカウントでログイン

2. **音声ファイルを準備**
   - GitHub Actions Artifactsから音声ファイル（MP3）をダウンロード
   - または、ローカルで生成した音声ファイルを使用

3. **新規投稿**
   - 「投稿」ボタンをクリック
   - 音声ファイルをアップロード
   - タイトル、説明文を入力（自動生成されたメタデータを使用）
   - 公開

### 半自動化（オプション）

詳細は `research/stand_fm_deep_research.md` の「アプローチA: Playwright自動化」を参照してください。

**注意**: Playwright自動化は規約違反のリスクがあります。実装前にstand.fm利用規約を確認してください。

---

## 7. note.com（半自動）

### 背景

note.comには音声投稿APIがないため、以下の半自動フローを推奨します:

1. 自動生成された音声ファイルを手動でnoteにアップロード
2. 自動生成された記事テンプレートをコピペ

### 記事テンプレート自動生成（実装予定）

```bash
# 将来的に実装予定
python scripts/generate_note_template.py --episode episodes/episode_technology_1.txt
```

テンプレート出力例:
```markdown
# 【ポッドキャスト】本日のテクノロジーニュース

> 📻 **音声版を聴く**
> [stand.fmで聴く](https://stand.fm/episodes/...)

## 本日のトピック

[自動生成された要約]

## 記事一覧

1. [記事タイトル1](URL) - 信頼度: 8.5/10
2. [記事タイトル2](URL) - 信頼度: 7.8/10

---

**📡 RSSフィード**: [購読する](https://taiyousan15.github.io/voice-automation/podcast/feed.xml)
```

---

## 自動配信の仕組み

### 初回登録後の動作

```
┌──────────────────────────────────────────────────────┐
│ GitHub Actions (毎日 06:00 JST)                      │
│   1. ニュース収集 (NewsData.io)                      │
│   2. 台本生成 (Groq LLM)                             │
│   3. 音声生成 (VOICEVOX Nemo) ← Phase 1で実装予定    │
│   4. RSS更新 (MP3 enclosure追加)                    │
│   5. GitHub Pages デプロイ                           │
└───────────────┬──────────────────────────────────────┘
                │
                ↓
┌──────────────────────────────────────────────────────┐
│ RSS Feed                                             │
│ https://taiyousan15.github.io/.../feed.xml          │
└───────────────┬──────────────────────────────────────┘
                │
                ↓ (各プラットフォームが自動監視)
┌─────────────────────────────────────────────────────┐
│ 自動配信                                            │
│   • Apple Podcasts   ✅ 新エピソード自動配信        │
│   • Spotify          ✅ 新エピソード自動配信        │
│   • Amazon Music     ✅ 新エピソード自動配信        │
│   • Google Podcasts  ✅ 新エピソード自動配信        │
│   • YouTube Podcasts ✅ 新エピソード自動配信        │
└─────────────────────────────────────────────────────┘
```

### RSSフィード更新頻度

- **パイプライン実行**: 毎日 06:00 JST（GitHub Actions Cron）
- **プラットフォーム監視**: 各プラットフォームが1-24時間ごとにRSSフィードをチェック
- **配信遅延**: 最大24時間（プラットフォームによる）

---

## トラブルシューティング

### 問題1: RSSフィードが見つからない

**症状**: プラットフォーム登録時に「RSS feed not found」エラー

**原因**: GitHub Pagesのデプロイが完了していない

**解決**:
1. ブラウザで `https://taiyousan15.github.io/voice-automation/podcast/feed.xml` にアクセス
2. HTTP 200 が返ってくることを確認
3. XMLが正しく表示されることを確認
4. 確認後、プラットフォーム登録を再試行

### 問題2: 音声ファイルが再生できない

**症状**: RSSフィードは読み込めるが、音声が再生できない

**原因**: MP3 enclosureタグが正しく生成されていない

**解決**:
1. RSSフィードのXMLを確認
2. `<enclosure>` タグが存在するか確認
3. `url` 属性が正しいMP3 URLか確認
4. `type="audio/mpeg"` が設定されているか確認
5. `length` 属性（ファイルサイズ）が設定されているか確認

### 問題3: プラットフォームで審査が通らない

**症状**: 審査で却下される

**よくある原因**:
1. カバーアートのサイズ不足（1400x1400px未満）
2. 音声ファイルが短すぎる（60秒未満）
3. 説明文が不適切
4. タイトルに禁止ワードが含まれる

**解決**:
1. 各プラットフォームのガイドラインを確認
2. エラーメッセージに従って修正
3. 再申請

---

## 次のステップ

### Phase 1完了後
1. 上記の手順で各プラットフォームにRSS URLを登録（初回のみ）
2. 毎日自動的に新エピソードが配信される
3. stand.fmとnote.comは手動または半自動で投稿

### Phase 2（オプション）
- stand.fm Playwright自動化の実装
- note.com記事テンプレート自動生成

### Phase 3（オプション）
- n8nワークフロー可視化
- エラー通知の自動化

---

**最終更新**: 2026-02-14T02:00:00+09:00
**担当**: Claude Sonnet 4.5
**ステータス**: Phase 1実装中
