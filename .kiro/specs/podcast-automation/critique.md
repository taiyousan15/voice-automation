# Critique

- **Score**: 73/100 (C=17, U=24, T=13, E=19)
- **Requirements found**: 4
- **Missing sections**: 0
- **Open questions**: 0
- **Banned words**: 1

## Issues

- 🔴 [high] **MISSING_REQ_FIELD**: REQ-900 に必須フィールド欠落: 受入テスト
- 🔴 [high] **MISSING_REQ_FIELD**: REQ-900 に必須フィールド欠落: 例外・エラー
- 🔴 [high] **MISSING_REQ_FIELD**: REQ-901 に必須フィールド欠落: 受入テスト
- 🔴 [high] **MISSING_REQ_FIELD**: REQ-901 に必須フィールド欠落: 例外・エラー
- 🔴 [high] **MISSING_REQ_FIELD**: REQ-902 に必須フィールド欠落: 受入テスト
- 🔴 [high] **MISSING_REQ_FIELD**: REQ-902 に必須フィールド欠落: 例外・エラー
- 🔴 [high] **MISSING_REQ_FIELD**: REQ-903 に必須フィールド欠落: 受入テスト
- 🔴 [high] **MISSING_REQ_FIELD**: REQ-903 に必須フィールド欠落: 例外・エラー
- 🟡 [medium] **AMBIGUOUS_WORDS**: 曖昧語が 1 個出現: [{'word': 'optimal', 'count': 1}]
- 🔴 [high] **NO_ACCEPTANCE_TEST**: REQ-900 に受入テストがありません
- 🔴 [high] **NO_ACCEPTANCE_TEST**: REQ-901 に受入テストがありません
- 🔴 [high] **NO_ACCEPTANCE_TEST**: REQ-902 に受入テストがありません
- 🔴 [high] **NO_ACCEPTANCE_TEST**: REQ-903 に受入テストがありません
- 🔴 [high] **EARS_NOT_OK**: REQ-901 の要件文(EARS)がEARSパターンに一致しません: システムは月間99パーセント以上の可用性を維持しなければならない。可用性は（正常実行日数 / 30日）× 100で計算される。ダウン時間合計は月間4.3時間以内に制限される。
- 🔴 [high] **EARS_NOT_OK**: REQ-902 の要件文(EARS)がEARSパターンに一致しません: システムのすべてのコードベースは、ユニットテスト・統合テスト・E2Eテストによって、80パーセント以上のコードカバレッジを達成しなければならない。関数の複雑度（Cyclomatic Complexity）は最大10以下に制限される。
- 🔴 [high] **EARS_NOT_OK**: REQ-903 の要件文(EARS)がEARSパターンに一致しません: システムの月間運用コスト（外部API + インフラ）は、選択したプランに従い、ゼロコスト版は1,600円以下、プロレベル品質版は44,000円以下に抑えなければならない。コスト超過が発生した場合は、翌月のAPI呼び出しを制限または段階的に削減しなければならない。

## Recommendations

- 目標スコア(98点)まであと 25 点必要です。
- **Completeness**: 必須セクション/フィールドを追加してください。
- **Unambiguity**: 曖昧語を具体的な数値/状態に置き換えてください。
- **Testability**: 全REQにGWT形式の受入テストを追加してください。
- **EARS**: 全REQの要件文をEARSパターンに準拠させてください。
