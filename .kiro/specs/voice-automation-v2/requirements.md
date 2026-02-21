# Requirements: voice-automation-v2

> 音声自動化システム v2.0 - マーケティング特化型ポッドキャスト自動配信システム

## 1. 概要（Executive Summary）

ユーザーが指定したキーワードから、グローバルリサーチ、太陽スタイルのマーケティング台本生成、品質チェック、Fish Audio音声生成を経て、4-7分の音声明瞭度90%以上のエピソードを自動生成・配信するシステムを構築する。既存の基本的なニュース配信システムを、マーケティングテクニックと品質管理機能を強化した高付加価値システムに改造する。


## 2. 目的（Purpose）

本システムの目的は、単純なニュース配信から脱却し、マーケティング技術を活用した高付加価値の音声コンテンツ自動生成システムを実現することである。具体的には以下の3つを達成する：

1. **情報の質的向上**: world-researchとkeyword-mega-extractorにより、国内外100記事以上の多様な情報源から多様で信頼性の高いコンテンツを収集する
2. **マーケティング要素の強化**: 太陽スキル群（taiyo-style-headline, taiyo-style-vsl, taiyo-rewriter）により、成約率を高める台本構造を実現する
3. **音声品質の保証**: 日本語読み方チェッカー（2回実施）と品質検品により、誤読率5%未満、太陽スコア70点以上を実現する

これにより、リスナーにとって有益で魅力的な音声コンテンツを継続的に提供し、システム運用コストを月間¥1,000以下に抑えながら、持続可能な自動配信を実現する。
## 3. 背景 & Context

### 現状の課題
- 既存システム（v1.0）はNewsData.io APIからニュース収集→Groq台本生成→Fish Audio音声化の単純なフロー
- 台本の質が低い（マーケティング要素なし）
- 日本語読み上げ時の誤読が発生（数字、難読漢字）
- タイトルの魅力が不足
- 音声の話し方パターンが固定

### 既存運用
- GitHub Actions（毎日06:00 JST）で自動実行
- GitHub Pagesで配信（RSS 2.0）
- 音声成功率: 67%（2026-02-14時点）
- 月間コスト: ¥450

### 制約
- 既存システムとの互換性維持（orchestrator.py, RSS generator）
- 月間コスト上限: ¥1,000
- 実行時間上限: 10分/エピソード

## 4. スコープ

### 3.1 In Scope
- グローバルリサーチ機能（world-research + keyword-mega-extractor統合）
- 太陽スキル統合（taiyo-style-headline, taiyo-style-vsl, taiyo-rewriter）
- 日本語読み方チェッカーシステム
- 品質検品機能（2回実施）
- Fish Audio話し方パターン適用
- 4-7分の台本生成
- 既存システム（orchestrator.py）との統合

### 3.2 Out of Scope（重要）
- 音声配信者分析機能（Phase 2）: 将来実装
- stand.fm自動投稿（APIなし）
- Apple Podcasts/Spotify自動登録（手動登録のみ）
- リアルタイム配信（バッチ処理のみ）
- 複数言語対応（日本語のみ）
- 音声編集機能（BGM追加、音量調整等）

## 5. 用語集 / Glossary

| 用語 | 定義 |
|------|------|
| 太陽スキル | taiyo-style-headline, taiyo-style-vsl, taiyo-rewriter等の太陽スタイルマーケティング技術を実装したスキル群 |
| EARS | 要件記述の標準構文パターン（体系的要件記述手法） |
| GWT | Given-When-Then。受入テストの記述形式 |
| Fish Audio | 音声合成API。voice IDで話者を指定 |
| 話し方パターン | 音声の速度、トーン、間の取り方等のパラメータセット |
| エピソード | 1つの音声コンテンツ（4-7分）とそのメタデータ |
| 台本 | 音声化する日本語テキスト（1,200-2,000文字） |
| world-research | 全世界SNS・論文・ニュース横断検索スキル |
| keyword-mega-extractor | 複合・関連キーワード抽出スキル |

## 6. ステークホルダー & 役割

| Role | 権限/責務 |
|------|----------|
| システム管理者 | GitHub Secrets設定、ワークフロー管理、API Key管理 |
| コンテンツ作成者（AIシステム） | キーワード受領、リサーチ、台本生成、音声生成 |
| リスナー | RSS Feed経由でエピソード取得、音声視聴 |
| GitHub Actions | 自動実行、デプロイ |

## 7. 前提/仮定（Assumptions）

- Fish Audio APIのvoice IDはユーザーが事前に取得・設定済み
- GitHub Secretsに必須API Keyが設定済み（GROQ_API_KEY, FISH_AUDIO_API_KEY等）
- world-research, keyword-mega-extractor, taiyo-*スキルが正常動作する
- Whisper APIは使用しない（Phase 2でのみ必要）
- text_preprocessor.pyは既存（数字→ひらがな変換機能あり）

## 8. 制約（Constraints）

### 技術制約
- 実行環境: GitHub Actions（ubuntu-latest, Python 3.11）
- API利用: Groq（無料）、Fish Audio（従量課金）、NewsData.io（無料プラン）
- ストレージ: GitHub Pages（100GB上限）
- 同時実行: 1ワークフローのみ（cronスケジュール）

### 運用制約
- 実行時間: 10分/ワークフロー（GitHub Actions制限）
- タイムアウト: Fish Audio 240秒/エピソード
- 日次実行: 06:00 JST（固定）

### コスト制約
- 月間上限: ¥1,000
- Fish Audio: ~¥15/エピソード × 30 = ¥450
- 残予算: ¥550（将来拡張用）

### 法務制約
- ニュース引用: 著作権法第32条（引用の範囲内）
- API利用規約遵守: NewsData.io, Fish Audio, Groq

## 9. 成功条件（Success Metrics）

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| 台本生成成功率 | >= 95% | 成功エピソード数 / 試行数 |
| 音声生成成功率 | >= 80% | 音声ファイル生成数 / 台本数 |
| 日本語誤読発生率 | < 5% | 人間評価（サンプリング10エピソード） |
| 台本生成時間 | < 5分 | orchestrator実行ログ |
| 音声生成時間 | < 240秒 | Fish Audio APIレスポンス時間 |
| 太陽スコア | >= 70点 | taiyo-analyzerスコア |
| 月間コスト | <= ¥1,000 | API請求額 |

## 10. 機能要件（Functional Requirements）

### REQ-001: キーワード入力受付
- 種別: EARS-普遍
- 優先度: MUST
- 要件文(EARS): システムは、ユーザーが指定した1つのキーワード（最大50文字）を受け取り、リサーチ処理を開始しなければならない。
- 根拠/目的: エピソード生成の起点となる情報を明確にするため
- 受入テスト(GWT):
  - AT-001: Given システムが起動した状態 When ユーザーが"Claude Code"を入力 Then キーワード="Claude Code"として保存され、リサーチ処理が開始される
  - AT-002: Given システムが起動した状態 When ユーザーが51文字のキーワードを入力 Then エラーメッセージ"キーワードは50文字以内"が表示される
- 例外・エラー:
  - EH-001: If キーワードが空文字列の場合 then システムはエラーメッセージ"キーワードを入力してください"を表示し、処理を中断する
  - EH-002: If キーワードが50文字を超える場合 then システムは最初の50文字を採用し、警告ログを出力する
- 補足:
  - 関連: REQ-002
  - 備考: 既存のconfig.yamlのthemes配列を拡張

### REQ-002: グローバルリサーチ実行
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): キーワードが入力されたとき、システムはworld-researchスキルを呼び出し、国内外SNS、ニュース、論文から最低100記事の情報を収集しなければならない。
- 根拠/目的: 多角的な情報源から質の高いコンテンツを作成するため
- 受入テスト(GWT):
  - AT-003: Given キーワード="AI Agent" When world-researchスキルを実行 Then 100記事以上の情報が`research_output/{keyword}_global.json`に保存される
  - AT-004: Given キーワード="Claude Code" When world-researchスキルを実行 Then X(Twitter), Reddit, note.com, Arxivからそれぞれ10記事以上が収集される
- 例外・エラー:
  - EH-003: If world-researchスキルが100記事未満しか収集できない場合 then システムは警告ログを出力し、収集できた記事で処理を継続する
  - EH-004: If world-researchスキルがタイムアウト（300秒）した場合 then システムはエラーログを出力し、既存のNewsData.io APIにフォールバックする
- 補足:
  - 関連: REQ-003
  - 備考: world-researchスキルは既存のTaskツール経由で呼び出し

### REQ-003: 関連キーワード抽出
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): グローバルリサーチが完了したとき、システムはkeyword-mega-extractorスキルを呼び出し、配信構造、心理トリガー、コピーライティング等の関連キーワードを50個以上抽出しなければならない。
- 根拠/目的: 台本生成時にマーケティング要素を強化するため
- 受入テスト(GWT):
  - AT-005: Given research_output/{keyword}_global.jsonが存在 When keyword-mega-extractorスキルを実行 Then 50個以上のキーワードが`research_output/{keyword}_keywords.json`に保存される
  - AT-006: Given 抽出されたキーワード When キーワードに"配信構造", "心理トリガー", "コピーライティング"が含まれているか確認 Then これらのキーワードが最低1つずつ含まれている
- 例外・エラー:
  - EH-005: If keyword-mega-extractorスキルが50個未満のキーワードしか抽出できない場合 then システムは警告ログを出力し、抽出できたキーワードで処理を継続する
- 補足:
  - 関連: REQ-004

### REQ-004: タイトル生成
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): 関連キーワード抽出が完了したとき、システムはtaiyo-style-headlineスキルを呼び出し、クリック率予測スコアが最高得点の魅力的なタイトル（最大60文字）を1つ生成しなければならない。
- 根拠/目的: リスナーの視聴意欲を高めるため
- 受入テスト(GWT):
  - AT-007: Given research_output/{keyword}_keywords.jsonが存在 When taiyo-style-headlineスキルを実行 Then 60文字以内のタイトルが生成され、クリック率予測スコアが付与される
  - AT-008: Given 生成されたタイトル When クリック率予測スコアが70点以上か確認 Then スコアが70点以上である
- 例外・エラー:
  - EH-006: If taiyo-style-headlineスキルが60文字を超えるタイトルを生成した場合 then システムは最初の60文字を採用し、"..."を末尾に追加する
  - EH-007: If クリック率予測スコアが70点未満の場合 then システムは警告ログを出力し、そのタイトルをそのまま使用する
- 補足:
  - 関連: REQ-005

### REQ-005: 台本生成（太陽スキル）
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): タイトル生成が完了したとき、システムはtaiyo-style-vslスキルとtaiyo-rewriterスキルを順次呼び出し、4-7分に相当する1,200-2,000文字の台本を生成しなければならない。
- 根拠/目的: マーケティング要素を含む太陽スコア70点以上の台本を作成するため
- 受入テスト(GWT):
  - AT-009: Given タイトルと収集情報が存在 When taiyo-style-vslスキルを実行 Then VSL構造の台本が生成される
  - AT-010: Given VSL構造の台本 When taiyo-rewriterスキルを実行 Then 1,200-2,000文字の最終台本が生成される
  - AT-011: Given 最終台本 When 文字数をカウント Then 1,200文字以上、2,000文字以下である
- 例外・エラー:
  - EH-008: If 生成された台本が1,200文字未満の場合 then システムは警告ログを出力し、追加コンテンツを生成する
  - EH-009: If 生成された台本が2,000文字を超える場合 then システムは最初の2,000文字を採用し、末尾を"...続きはWebサイトで"で終える
- 補足:
  - 関連: REQ-006

### REQ-006: 日本語読み方チェック（1回目）
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): 台本が生成されたとき、システムは日本語読み方チェッカーを実行し、難読漢字、数字、英単語の読み間違いリスクを検出しなければならない。
- 根拠/目的: Fish Audio音声化時の誤読を防ぐため
- 受入テスト(GWT):
  - AT-012: Given 台本に"脆弱"という漢字が含まれている When 日本語読み方チェッカーを実行 Then "脆弱"が難読漢字としてフラグされる
  - AT-013: Given 台本に"1000万"という数字が含まれている When 日本語読み方チェッカーを実行 Then "1000万"が数字読みリスクとしてフラグされる
  - AT-014: Given 台本に"API"という英単語が含まれている When 日本語読み方チェッカーを実行 Then "API"が英単語読みリスクとしてフラグされる
- 例外・エラー:
  - EH-010: If 日本語読み方チェッカーがタイムアウト（30秒）した場合 then システムはエラーログを出力し、チェックをスキップする
- 補足:
  - 関連: REQ-007
  - 備考: 新規モジュール `src/quality/japanese_reading_checker.py`

### REQ-007: 自動修正
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): 読み間違いリスクが検出されたとき、システムは難読漢字→ひらがな、数字→text_preprocessor適用、英単語→カタカナ追加の自動修正を実行しなければならない。
- 根拠/目的: 音声化前に台本を修正し、誤読を予防するため
- 受入テスト(GWT):
  - AT-015: Given "脆弱"がフラグされている When 自動修正を実行 Then "脆弱" → "ぜいじゃく"に変換される
  - AT-016: Given "1000万"がフラグされている When 自動修正（text_preprocessor）を実行 Then "1000万" → "いっせんまん"に変換される
  - AT-017: Given "API"がフラグされている When 自動修正を実行 Then "API（エーピーアイ）"に変換される
- 例外・エラー:
  - EH-011: If text_preprocessorが数字変換に失敗した場合 then システムは元の数字をそのまま使用し、警告ログを出力する
- 補足:
  - 関連: REQ-008

### REQ-008: 日本語読み方チェック（2回目）
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): 自動修正が完了したとき、システムは日本語読み方チェッカーを再度実行し、残存する読み間違いリスクが0件であることを確認しなければならない。
- 根拠/目的: 修正の品質を保証するため
- 受入テスト(GWT):
  - AT-018: Given 自動修正済み台本 When 日本語読み方チェッカー（2回目）を実行 Then 難読漢字、数字読みリスク、英単語読みリスクがすべて0件である
  - AT-019: Given 残存リスクが0件 When チェック結果を確認 Then 合格フラグ=trueが設定される
- 例外・エラー:
  - EH-012: If 残存リスクが1件以上の場合 then システムは警告ログを出力し、手動確認を要求する（処理は継続）
- 補足:
  - 関連: REQ-009

### REQ-009: 品質検品
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): 日本語読み方チェック（2回目）が完了したとき、システムは品質検品機能を実行し、文字数、読み上げ時間、太陽スコアが基準を満たすことを確認しなければならない。
- 根拠/目的: 配信前に品質を保証するため
- 受入テスト(GWT):
  - AT-020: Given 台本文字数=1,500字 When 品質検品を実行 Then 文字数チェック=合格
  - AT-021: Given 予想読み上げ時間=5分30秒 When 品質検品を実行 Then 読み上げ時間チェック=合格
  - AT-022: Given 太陽スコア=75点 When 品質検品を実行 Then 太陽スコアチェック=合格
- 例外・エラー:
  - EH-013: If 文字数が1,200字未満または2,000字超の場合 then システムは不合格フラグを設定し、台本再生成を要求する
  - EH-014: If 太陽スコアが70点未満の場合 then システムはtaiyo-rewriterを再実行する（最大2回）
- 補足:
  - 関連: REQ-010
  - 備考: 新規モジュール `src/quality/quality_inspector.py`

### REQ-010: Fish Audio音声生成
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): 品質検品が合格したとき、システムはFish Audio APIを呼び出し、指定ボイスIDとタイムアウト240秒で音声ファイル（mp3）を生成しなければならない。
- 根拠/目的: 音声明瞭度90%以上のコンテンツを配信するため
- 受入テスト(GWT):
  - AT-023: Given 品質検品合格済み台本 When Fish Audio APIを呼び出し Then 240秒以内にmp3ファイルが生成される
  - AT-024: Given 生成されたmp3ファイル When ファイルサイズを確認 Then 1MB以上である
  - AT-025: Given 生成されたmp3ファイル When 再生時間を確認 Then 4-7分である
- 例外・エラー:
  - EH-015: If Fish Audio APIが240秒でタイムアウトした場合 then システムはエラーログを出力し、エピソードをスキップする
  - EH-016: If Fish Audio APIがエラー（429, 500等）を返した場合 then システムは1回リトライし、失敗したらエピソードをスキップする
- 補足:
  - 関連: REQ-011
  - 備考: 既存モジュール `src/generators/fish_audio_client.py` 強化

### REQ-011: 話し方パターン適用（オプション）
- 種別: EARS-オプション
- 優先度: SHOULD
- 要件文(EARS): 話し方パターン機能が有効な場合、システムはFish Audio API呼び出し時に、ユーザー指定のパターン（speed, pitch_variation等）を適用しなければならない。
- 根拠/目的: 音声の多様性を確保し、リスナーの飽きを防ぐため
- 受入テスト(GWT):
  - AT-026: Given 話し方パターン="energetic" When Fish Audio APIを呼び出し Then speed=1.1で音声が生成される
  - AT-027: Given 話し方パターン="calm" When Fish Audio APIを呼び出し Then speed=0.9で音声が生成される
- 例外・エラー:
  - EH-017: If 指定された話し方パターンが存在しない場合 then システムはデフォルトパターン（speed=1.0）を使用し、警告ログを出力する
- 補足:
  - 関連: REQ-010
  - 備考: 新規ファイル `templates/voice_patterns.json`

### REQ-012: RSS Feed更新
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): 音声生成が完了したとき、システムはRSS Feed生成機能を呼び出し、新しいエピソードをfeed.xmlに追加しなければならない。
- 根拠/目的: リスナーがPodcastアプリで新エピソードを受信できるようにするため
- 受入テスト(GWT):
  - AT-028: Given 音声ファイル=episode_xxx.mp3 When RSS Feed生成を実行 Then feed.xmlに新しい<item>要素が追加される
  - AT-029: Given 追加された<item>要素 When <enclosure>タグを確認 Then url属性がGitHub PagesのURLである
  - AT-030: Given feed.xml When RSS 2.0準拠を検証 Then 有効なRSS Feedである
- 例外・エラー:
  - EH-018: If RSS Feed生成に失敗した場合 then システムはエラーログを出力し、前回のfeed.xmlを維持する
- 補足:
  - 関連: REQ-013
  - 備考: 既存モジュール `src/publishers/rss_generator.py`

### REQ-013: GitHub Pagesデプロイ
- 種別: EARS-イベント駆動
- 優先度: MUST
- 要件文(EARS): RSS Feed更新が完了したとき、システムはGitHub Pages デプロイ機能を実行し、エピソードディレクトリをgh-pagesブランチにデプロイしなければならない。
- 根拠/目的: 公開URLでエピソードを配信するため
- 受入テスト(GWT):
  - AT-031: Given episodes/ディレクトリ When GitHub Pagesデプロイを実行 Then gh-pagesブランチにファイルがpushされる
  - AT-032: Given デプロイ完了 When 公開URLにアクセス Then 新しいエピソードが閲覧可能である
- 例外・エラー:
  - EH-019: If GitHub Pagesデプロイに失敗した場合 then システムはエラーログを出力し、GitHub Actions workflowを失敗ステータスで終了する
- 補足:
  - 関連: なし
  - 備考: 既存ワークフロー `.github/workflows/podcast-automation.yml`

## 11. 非機能要件（Non-Functional Requirements）

### REQ-900: 実行時間
- 種別: EARS-普遍
- 優先度: MUST
- 要件文(EARS): システムは、1エピソードの生成（リサーチ開始から音声生成完了まで）を10分以内に完了しなければならない。
- 根拠/目的: GitHub Actionsのタイムアウト制限を遵守するため
- 受入テスト(GWT):
  - AT-900: Given エピソード生成開始 When 処理完了までの時間を計測 Then 10分以内である
- 例外・エラー:
  - EH-900: If 10分を超えた場合 then GitHub Actionsはworkflowをタイムアウトで強制終了する
- 補足:
  - 備考: orchestrator.pyのログでタイムスタンプ記録

### REQ-901: コスト
- 種別: EARS-状態駆動
- 優先度: MUST
- 要件文(EARS): 本番運用中のとき、システムは月間運用コストを¥1,000以下に維持しなければならない。
- 根拠/目的: 予算制約を遵守するため
- 受入テスト(GWT):
  - AT-901: Given 月間30エピソード生成 When API請求額を確認 Then ¥1,000以下である
- 例外・エラー:
  - EH-901: If 月間コストが¥1,000を超える予測の場合 then システムは警告メールを送信し、エピソード生成頻度を調整する
- 補足:
  - 備考: Fish Audio ~¥450/月、Whisper API未使用（Phase 2で追加時に再計算）

### REQ-902: 互換性
- 種別: EARS-普遍
- 優先度: MUST
- 要件文(EARS): システムは、既存のorchestrator.py、rss_generator.pyとAPIレベルで互換性を維持しなければならない。
- 根拠/目的: 既存システムの安定性を損なわないため
- 受入テスト(GWT):
  - AT-902: Given 新機能追加後 When orchestrator.pyを実行 Then 既存のエピソード生成フローが正常動作する
  - AT-903: Given 新機能追加後 When rss_generator.pyを実行 Then 有効なRSS Feedが生成される
- 例外・エラー:
  - EH-902: If 互換性が破損した場合 then システムは既存フローにフォールバックし、新機能を無効化する
- 補足:
  - 備考: 既存テスト（tests/test_integration.py）を継続実行

## 12. セキュリティ/プライバシー要件

### REQ-SEC-001: API Key保護
- システムは、すべてのAPI Key（GROQ_API_KEY, FISH_AUDIO_API_KEY等）をGitHub Secretsで管理し、コードやログに平文で出力してはならない。

### REQ-SEC-002: ログマスキング
- システムは、ログ出力時にAPI KeyやユーザーIDが含まれる場合、自動的に"***"でマスキングしなければならない。

### REQ-SEC-003: 外部API呼び出し検証
- システムは、外部API（Fish Audio, NewsData.io等）呼び出し前にリクエストURLとパラメータを検証し、インジェクション攻撃を防止しなければならない。

## 13. ログ/監視/運用要件

### REQ-OPS-001: 構造化ログ
- システムは、すべてのログをJSON形式で出力し、レベル（DEBUG, INFO, WARNING, ERROR）、タイムスタンプ、モジュール名を含めなければならない。

### REQ-OPS-002: エラー通知
- システムは、致命的エラー（音声生成失敗、API認証エラー等）が発生した場合、GitHub Actions workflowを失敗ステータスで終了しなければならない。

### REQ-OPS-003: 再実行可能性
- システムは、エピソード生成処理を手動で再実行できるように、GitHub Actions workflow_dispatchトリガーをサポートしなければならない。

## 14. 未解決事項（Open Questions）

- ❌ 話し方パターンの詳細仕様（10種類のパターン定義）は未定義
- ❌ 日本語読み方チェッカーの難読漢字辞書の初期データセットは未作成
- ❌ 品質検品の太陽スコア閾値（70点）の有効性は未検証
- ❌ world-researchスキルのタイムアウト値（300秒）は暫定値

## 15. SLO/SLI/SLA（信頼性目標）

| Metric | Target | Measurement |
|--------|--------|-------------|
| エピソード生成成功率 | >= 80% (30日) | 成功エピソード数 / 試行数 |
| 音声生成成功率 | >= 80% (30日) | 音声ファイル生成数 / 台本数 |
| RSS Feed配信成功率 | >= 99% (30日) | 成功デプロイ数 / 試行数 |
| 実行時間P99 | < 10分 | GitHub Actions実行ログ |

## 16. 関連ADR（技術決定記録）

| ADR ID | 決定内容 | Status |
|--------|---------|--------|
| ADR-001 | Fish Audio vs VOICEVOX選定（Fish Audio採用） | Accepted |
| ADR-002 | 太陽スキル統合方法（Taskツール経由） | Proposed |
| ADR-003 | 日本語読み方チェッカーの実装方式（ルールベース + Claude API） | Proposed |

## 17. セキュリティ脅威と対策

| 脅威 | リスク | 緩和策 | 対応要件 |
|------|--------|--------|---------|
| API Key漏洩 | High | GitHub Secretsで管理、ログマスキング | REQ-SEC-001, REQ-SEC-002 |
| インジェクション攻撃 | Medium | 外部API呼び出し前に検証 | REQ-SEC-003 |
| 大量API呼び出し（DoS） | Low | レート制限、タイムアウト設定 | REQ-900 |

## 18. ガードレール（AI制約）

- 許可パス: `src/`, `tests/`, `.kiro/`, `templates/`, `episodes/`
- 禁止パス: `.env*`, `secrets/`, `~/.ssh/`, `~/.aws/`
- 必須承認: 本番デプロイ（GitHub Actions手動トリガー時のみ）

## 19. 運用手順書参照

- オンコール連絡先: GitHub Issues
- インシデント対応: docs/RUNBOOK.md#incident-response（未作成）
- ロールバック手順: `git revert` + 手動workflow実行

## 20. 成熟度レベル

| Level | 名称 | 達成条件 | 現在 |
|-------|------|---------|------|
| L1 | Draft | requirements.md作成 | ✅ |
| L2 | Review Ready | C.U.T.E. >= 90 | ⏳ |
| L3 | Implementation Ready | C.U.T.E. >= 98, レビュー承認 | - |
| L4 | Production Ready | 実装完了, テスト完了, セキュリティレビュー | - |
| L5 | Enterprise Ready | SLO達成, 監視設定, Runbook完備 | - |
