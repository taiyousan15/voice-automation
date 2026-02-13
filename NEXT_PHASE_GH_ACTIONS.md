# GH-ACTIONS-001: GitHub Actions ワークフロー実装

**Status**: Ready for Implementation
**Depends On**: PIPELINE-001 ✅ (COMPLETED in ba8134a)
**Target**: Week 2 - GitHub Actions integration

---

## 概要

PIPELINE-001で完成したエンドツーエンド統合パイプラインを、GitHub Actionsで自動スケジューリング・実行するための実装。

### 目的
- 毎日 06:00 JST に自動的にパイプライン実行
- Artifacts に出力ファイル保存
- Failure notification に対応
- Retry 機構の実装

---

## 実装スコープ

### 1. GitHub Actions Workflow定義
**ファイル**: `.github/workflows/podcast-automation.yml`

```yaml
name: Podcast Automation Pipeline

on:
  schedule:
    - cron: '0 21 * * *'  # 06:00 JST = 21:00 UTC前日
  workflow_dispatch:  # Manual trigger

jobs:
  pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run Pipeline
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          NEWSDATA_API_KEY: ${{ secrets.NEWSDATA_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          python scripts/run_pipeline.py --themes technology,business,health

      - name: Upload Artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: podcast-outputs-${{ github.run_id }}
          path: episodes/
          retention-days: 30

      - name: Notify Slack on Failure
        if: failure()
        run: |
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -H 'Content-Type: application/json' \
            -d '{"text":"❌ Podcast pipeline failed"}'
```

---

## 実装ステップ

### Phase 1: GitHub Actions Secrets登録
1. GitHub Settings → Secrets and variables → Actions
2. 以下を登録：
   - `GROQ_API_KEY`
   - `NEWSDATA_API_KEY`
   - `OPENROUTER_API_KEY`
   - `SLACK_WEBHOOK` (オプション)

### Phase 2: Workflow YAML作成
1. `.github/workflows/podcast-automation.yml` を作成
2. Cron スケジュール設定 (06:00 JST = 21:00 UTC前日)
3. Python 環境セットアップ
4. パイプライン実行
5. Artifacts アップロード

### Phase 3: テスト実行
1. Manual trigger で動作確認
2. Logs 確認
3. Artifacts 出力確認

### Phase 4: エラーハンドリング
1. Retry 機構 (max-attempts: 3)
2. Timeout 対応 (timeout-minutes: 10)
3. Slack notification (failure)

---

## テスト方法

### 1. ローカル実行確認
```bash
# GitHub Actions を実行することなく、パイプラインが動作するか確認
python scripts/run_pipeline.py --themes technology

# Expected output:
# 🚀 PODCAST AUTOMATION PIPELINE STARTED
# ...
# ✅ PIPELINE EXECUTION COMPLETED
```

### 2. GitHub Actions Manual Trigger
GitHub Repository → Actions → Podcast Automation Pipeline → Run workflow

### 3. スケジュール確認
毎日 06:00 JST に自動実行されることを確認

---

## 期待される成果物

### ✅ 出力ファイル（Artifacts）
- `episode_*.txt` - ポッドキャスト台本
- `feed.xml` - RSS 2.0 フィード
- `summary.json` - メタデータ
- `dashboard.json` - 実行結果

### ✅ ログ
- GitHub Actions Logs で実行結果を確認可能
- 失敗時は Slack notification

### ✅ 成功基準
- Cron トリガーで毎日 06:00 JST 実行
- Pipeline 完了時間 < 10分
- Artifacts に全ファイル保存
- Failure 時は notification

---

## 次のフェーズ向け

### RSS-001（Week 2, Day 2）
- RSS フィード を GitHub Pages にデプロイ
- GitHub Pages ホスティング設定
- RSS feed URL: `https://<username>.github.io/podcast-automation/feed.xml`

### INTEGRATION-001（Week 2, Day 3-4）
- stand.fm 連携（RSS 取り込み）
- note.com テンプレート出力

---

## トラブルシューティング

### GitHub Actions 失敗時
1. **Secrets not found** → Settings で再確認
2. **Python import error** → `pip install -r requirements.txt` 実行確認
3. **API rate limit** → NewsData.io quota 確認
4. **Timeout** → timeout-minutes を増加させる

---

## PC再起動後の再開手順

1. **ローカル環境確認**
   ```bash
   cd /Users/matsumototoshihiko/Desktop/開発2026/音声自動化システム
   git status  # ba8134a commit確認
   python scripts/run_pipeline.py --dry-run  # 動作確認
   ```

2. **GitHub設定**
   - リモートリポジトリを作成（未作成の場合）
   - Workflow YAML を `.github/workflows/` に配置
   - Secrets を GitHub Settings で登録

3. **テスト実行**
   - Manual trigger で実行確認
   - Artifacts ダウンロード確認
   - ログ確認

---

**作成日**: 2026-02-13
**Status**: Ready for Implementation
**Estimated Effort**: 2-3 hours
