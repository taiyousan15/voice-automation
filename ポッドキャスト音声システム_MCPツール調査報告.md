# ポッドキャスト・音声配信システム構築用MCPツール 徹底調査レポート

調査日: 2026年2月11日

---

## 目次

1. [音声文字起こし（Speech-to-Text）](#音声文字起こしspeech-to-text)
2. [音声合成（Text-to-Speech）](#音声合成text-to-speech)
3. [RSS・ニュースフィード](#rssニュースフィード)
4. [Webスクレイピング・コンテンツ抽出](#webスクレイピングコンテンツ抽出)
5. [YouTube関連](#youtube関連)
6. [ポッドキャスト専門ツール](#ポッドキャスト専門ツール)

---

## 音声文字起こし（Speech-to-Text）

### 1. Audio Transcriber MCP (OpenAI Whisper)

**URL**: https://mcp.so/server/audio-transcriber-mcp/Ichigo3766

**機能**:
- OpenAI Whisper APIを使用した音声文字起こし
- ISO-639-1言語コードで多言語対応
- 文字起こし結果をファイル保存可能
- `transcribe_audio`ツールによる自動変換

**価格**:
- **無料** - MITライセンスのオープンソース
- OpenAI Whisper API利用時に従量課金が発生

**インストール**:
```bash
git clone https://github.com/Ichigo3766/audio-transcriber-mcp.git
npm install
npm run build
```

**必要なAPI**: OpenAI APIキー（Whisper API）

**ポッドキャスト活用例**:
- ポッドキャストエピソードの自動文字起こし
- 会議やインタビュー音声の記録化
- アクセシビリティ向上のための字幕生成
- SEO対策用テキストコンテンツ作成

---

### 2. Local Speech-to-Text MCP Server (whisper.cpp)

**URL**: https://mcp.so/server/local-stt-mcp/SmartLittleApps

**機能**:
- **100%ローカル処理** - クラウドAPI不要、完全プライバシー保護
- Apple Silicon最適化で15倍以上の高速化
- 複数話者識別（Speaker Diarization）
- MP3、M4A、FLAC、OGG対応
- txt、json、vtt、srt、csv出力
- 2GB未満の低メモリ使用量

**価格**:
- **完全無料** - MITライセンス

**インストール**:
```bash
git clone https://github.com/SmartLittleApps/local-stt-mcp.git
npm install
npm run build
npm run setup:models
brew install whisper-cpp  # macOS
```

**必要なAPI**:
- 話者識別機能のみHuggingFaceトークン（無料）が必要

**ポッドキャスト活用例**:
- 複数ゲストの発言を自動識別
- オフラインでの文字起こし処理
- 低コストで大量エピソードを処理
- 字幕ファイル（SRT/VTT）の自動生成

---

### 3. Audio Transcription Server (多言語対応)

**URL**: https://mcpmarket.com/server/mcp-5

**機能**:
- 複数エンジン対応：Alibaba Cloud、OpenAI Whisper、iFlytek
- 多様な音声フォーマット対応
- 音声からテキストへの変換

**価格**: エンジンによる（各APIサービスの料金体系に依存）

**ポッドキャスト活用例**:
- 複数の文字起こしエンジンを使い分け
- 特定言語に強いエンジンを選択

---

## 音声合成（Text-to-Speech）

### 4. ElevenLabs MCP Server（公式）

**URL**: https://mcp.so/server/elevenlabs-mcp/elevenlabs

**機能**:
- 高品質AI音声合成
- ボイスクローニング
- オーディオ文字起こし
- 複数MCPクライアント対応（Claude、Cursor、Windsurf、OpenAI Agents）

**価格**:
- **フリープラン**: 毎月10,000クレジット無料
- 有料プラン: 追加クレジット購入可能

**インストール**:
```bash
# uvパッケージマネージャー経由
uvx elevenlabs-mcp
```

**必要なAPI**: ElevenLabs APIキー（elevenlabs.io/appで取得）

**ポッドキャスト活用例**:
- ナレーション音声の自動生成
- ゲスト音声のクローン作成
- 多言語ポッドキャスト制作
- 一貫した音声ブランディング

---

### 5. Kokoro TTS MCP Server（ローカル高品質）

**URL**: https://mcp.so/server/kokoro-tts-mcp/mberg

**機能**:
- 82百万パラメータの高品質TTS
- ONNXモデルでローカル実行
- 米英アクセント対応（男女複数ボイス）
- MP3ファイル生成
- オプションでS3アップロード
- 速度・音声・言語カスタマイズ

**価格**:
- **完全無料** - オープンソース

**インストール**:
- Kokoro ONNXウェイト（kokoro-v1.0.onnx、voices-v1.0.bin）をダウンロード
- ffmpegインストール必須
- UV経由で実行

**必要なAPI**:
- AWS認証情報（S3アップロード使用時のみ）

**ポッドキャスト活用例**:
- オフラインでの音声生成
- コスト無しで大量の音声コンテンツ制作
- ビデオナレーション自動生成
- インタロやアウトロの音声作成

---

### 6. Edge TTS MCP Server（Microsoft）

**URL**: 参考 - https://mcpmarket.com/server/edge-tts

**機能**:
- Microsoft Edge TTSエンジン利用
- 複数言語・音声対応
- 速度・ピッチ調整（±20%、Hz単位）
- MP3形式で音声生成
- 字幕ファイル自動生成

**価格**:
- **無料** - Microsoftのサービスを利用

**インストール**:
```bash
pip install "edge_tts_mcp_server"
edge-tts-mcp --host 0.0.0.0 --port 8080 --reload
```

**必要なAPI**: 不要

**ポッドキャスト活用例**:
- 無料で自然な音声合成
- 多言語対応ポッドキャスト制作
- 字幕と音声の同時生成

---

### 7. Local Voice MCP（Chatterbox TTS）

**URL**: https://mcp.so/server/local-voice-mcp/CodeCraftersLLC

**機能**:
- Chatterbox TTS使用の高品質音声
- ボイスクローニング
- プロソディ（抑揚）コントロール
- ElevenLabs互換REST API
- 一時ファイル自動削除
- MCP/HTTPサーバー双方向動作

**価格**:
- **無料** - MITライセンス

**インストール**:
```bash
npm install -g local-voice-mcp
# または
npx -y @codecraftersllc/local-voice-mcp
```

**必要な環境**: Node.js 16+、Python 3.8+、PyTorch、Chatterbox TTS

**ポッドキャスト活用例**:
- オーディオブック制作
- インタラクティブボイスレスポンス
- ローカル環境での音声インタラクション

---

### 8. MCP TTS Server（統合型）

**URL**: https://mcp.so/server/MCP_tts_server

**機能**:
- Kokoro TTS（ローカル）とOpenAI TTS（クラウド）の統一インターフェース
- リアルタイムストリーミング音声再生
- 音声選択、速度調整、再生制御
- MCPプロトコル対応

**価格**:
- **基本無料**（Kokoro TTS使用時）
- OpenAI TTS使用時は従量課金

**インストール**:
- Python 3.10以上
- uvパッケージマネージャー
- `.env`ファイルでOpenAI APIキー設定

**ポッドキャスト活用例**:
- ローカルとクラウドTTSの使い分け
- チャットボットへのTTS統合
- 教育コンテンツの音声生成

---

### 9. mcp-tts（マルチエンジン対応）

**URL**: https://mcp.so/server/mcp-tts/blacktop

**機能**:
- **4つのTTSエンジンサポート**:
  - say_tts（macOS組み込み）
  - elevenlabs_tts（ElevenLabs）
  - google_tts（Gemini 30種類の音声）
  - openai_tts（OpenAI 6種類の音声）
- 速度制御（0.25倍～4.0倍）
- カスタム音声指示

**価格**:
- **無料**（各APIサービスは別途料金）

**インストール**:
```bash
go install github.com/blacktop/mcp-tts@latest
```

**必要なAPI**: ElevenLabs、Gemini、OpenAI各APIキー

**ポッドキャスト活用例**:
- 複数TTSエンジンの一元管理
- 状況に応じた最適エンジン選択

---

### 10. MCP TTS Say

**URL**: https://mcp.so/server/mcp-tts-say

**機能**:
- OpenAI TTS SDK利用
- ローカル環境での音声再生
- 高品質音声合成

**価格**:
- **無料** - MITライセンス
- OpenAI API従量課金

**インストール**:
```bash
git clone https://github.com/hirokidaichi/mcp-tts-say.git
npm install
npm run dev
```

**必要なAPI**: OpenAI APIキー

**ポッドキャスト活用例**:
- 記事の音声版作成
- テキストコンテンツのオーディオ化

---

## RSS・ニュースフィード

### 11. MCP-RSS-Crawler

**URL**: https://mcp.so/server/mcp-rss-crawler

**機能**:
- 自動フィード取得とキャッシング（SQLite）
- 複数フィード管理（追加・更新・削除）
- キーワードフィルタリング
- Firecrawl統合による記事取得

**価格**:
- **無料** - オープンソース
- Firecrawl API利用時は別途料金

**インストール**:
```bash
git clone [リポジトリURL]
bun install
```

**必要なAPI**: Firecrawl APIキー

**ポッドキャスト活用例**:
- ニュースポッドキャスト素材の自動収集
- 複数ソースからのトピック集約
- キーワードベースのコンテンツフィルタリング
- LLMへのリアルタイム情報提供

---

### 12. News API MCP Server

**URL**: https://mcp.so/server/news_mcp/kcjonnyc

**機能**:
- NewsAPI.org経由で数百万記事を検索
- ヘッドライン取得
- ニュースソースの発見とフィルタリング

**価格**:
- **無料プラン**: 1日100リクエストまで
- 有料プラン: 追加リクエスト可能

**インストール**:
```bash
npm install
npm run build
```

**必要なAPI**: NewsAPI.org APIキー（無料登録）

**ポッドキャスト活用例**:
- ニュースポッドキャストの自動スクリプト生成
- 最新トピックの自動収集
- 複数ソースからの情報集約

---

### 13. RSS Feed MCP（feed-mcp）

**URL**: https://mcpservers.org/servers/richardwooding/feed-mcp

**機能**:
- RSS、Atom、JSONフィード対応
- ポッドキャストフィード読み込み
- ニュース・ブログ更新の自動追跡

**価格**: 無料（詳細不明）

**ポッドキャスト活用例**:
- 競合ポッドキャストの更新監視
- 業界ニュースの自動収集
- AIとの会話内で直接フィード確認

---

### 14. RSS Reader MCP

**URL**: https://github.com/kwp-lab/rss-reader-mcp

**機能**:
- RSSフィード集約
- 記事コンテンツ抽出
- Markdown形式で記事内容取得

**価格**: 無料（npmパッケージ）

**インストール**:
```bash
npm install rss-reader-mcp
```

**ポッドキャスト活用例**:
- RSSフィードからフルテキスト抽出
- ポッドキャストエピソード情報の自動取得

---

## Webスクレイピング・コンテンツ抽出

### 15. Firecrawl MCP Server（公式）

**URL**: https://mcp.so/server/firecrawl-mcp-server

**機能**:
- Webスクレイピング、クロール、ディスカバリー
- 検索とコンテンツ抽出
- 深層リサーチ
- バッチスクレイピング
- 自動リトライとレート制限
- クラウド・自ホスト対応

**10種類のツール**:
1. scrape - 単一ページ抽出
2. batch_scrape - 複数URL一括
3. map - URL発見
4. crawl - 非同期クロール
5. search - Web検索
6. extract - 構造化データ抽出
7. deep_research - インテリジェント調査
8. generate_llmstxt - LLMs.txt生成

**価格**:
- Firecrawl APIキー必要（クラウド版は有料の可能性）

**インストール**:
```bash
npm install -g firecrawl-mcp
# または
npx -y firecrawl-mcp
```

**必要なAPI**: Firecrawl APIキー（firecrawl.dev）

**ポッドキャスト活用例**:
- ポッドキャストトピック用のリサーチ自動化
- ニュースサイトからコンテンツ抽出
- 競合分析・トレンド調査
- ゲスト情報の自動収集

---

### 16. Crawl4AI MCP Server

**URL**: https://mcp.so/server/Crawl4AI-MCP/Vistiqx

**機能**:
- LLMベースのコンテンツ抽出
- Markdown、テキストスニペット抽出
- スマート抽出機能
- AIエージェント統合設計

**価格**: 詳細不明

**ポッドキャスト活用例**:
- 学術資源からの情報抽出
- 競合コンテンツ分析

---

### 17. Serper Search and Scrape MCP

**URL**: https://mcp.so/server/mcp-server-serper

**機能**:
- Serper APIでWeb検索
- Webページスクレイピング

**価格**: Serper API料金に依存

**ポッドキャスト活用例**:
- トピックリサーチの自動化
- 検索結果からコンテンツ抽出

---

## YouTube関連

### 18. YouTube Transcript Server（kimtaeyoon83）

**URL**: https://github.com/kimtaeyoon83/mcp-server-youtube-transcript

**機能**:
- **外部依存なし**で文字起こし取得
- 標準YouTube、Shorts、ビデオID対応
- 言語指定と自動フォールバック
- タイムスタンプ付与オプション
- **広告・スポンサーシップ自動フィルタリング**（デフォルト有効）
- チャプターマーカーベースの広告除去

**価格**:
- **完全無料** - 外部API不要

**インストール**:
```bash
# Smithery経由
npx -y @smithery/cli install @kimtaeyoon83/mcp-server-youtube-transcript --client claude

# 手動
npx -y @kimtaeyoon83/mcp-server-youtube-transcript
```

**必要なAPI**: 不要

**ポッドキャスト活用例**:
- 他ポッドキャスターのコンテンツ研究
- YouTube動画からポッドキャストエピソード作成
- 広告部分を除外した純粋なコンテンツ抽出
- インタビュー動画の文字起こし

---

### 19. YouTube Transcript MCP（jkawamoto）

**URL**: https://github.com/jkawamoto/mcp-youtube-transcript

**機能**:
- YouTubeビデオURLから文字起こし取得
- 50,000文字超過時の自動分割
- next_cursor機能で続きを取得

**価格**: 無料

**ポッドキャスト活用例**:
- 長時間動画の文字起こし
- エピソードごとの分割処理

---

### 20. YouTube Transcript Extractor（Smithery）

**URL**: https://smithery.ai/server/@alfie-max/youtube-mcp

**機能**:
- 構造化された文字起こし抽出
- 高度なフィルタリング
- トークンセーフなデフォルト設定
- タイムスタンプ付きキャプション
- 多言語サポート

**価格**: 無料

**ポッドキャスト活用例**:
- AI向けに最適化された文字起こし取得
- 多言語ポッドキャストコンテンツ収集

---

### 21. YouTube Transcribe MCP

**URL**: https://mcpmarket.com/server/youtube-transcribe

**機能**:
- YouTube公式文字起こし取得
- 公式字幕がない場合はOpenAI Whisperでローカル文字起こし

**価格**:
- YouTube API部分は無料
- Whisper使用時は従量課金

**ポッドキャスト活用例**:
- 字幕なし動画の文字起こし
- 公式字幕とWhisperのハイブリッド活用

---

## ポッドキャスト専門ツール

### 22. Podcast Intelligence Aggregator（Apify）

**URL**: https://apify.com/benthepythondev/podcast-intelligence-aggregator/api/mcp

**機能**:
- iTunes/Apple Podcastsからデータ抽出
- RSSフィード直接解析
- キーワード検索
- ID指定でのルックアップ
- エピソード、メタデータ、アナリティクス取得

**価格**: Apify料金プランに依存

**ポッドキャスト活用例**:
- 競合ポッドキャストの分析
- 業界トレンド調査
- エピソード情報の自動収集
- Apple Podcastsメタデータ取得

---

### 23. Podcast API MCP（Apify）

**URL**: https://apify.com/vivid_astronaut/podcast/api/mcp

**機能**:
- ポッドキャストメタデータ取得
- エピソード情報抽出

**価格**: Apify料金プランに依存

**ポッドキャスト活用例**:
- ポッドキャストカタログの構築
- エピソード管理の自動化

---

### 24. Podcast Episode Extractor（Apify）

**URL**: https://apify.com/simplifysme/podcast-episode-extractor/api/mcp

**機能**:
- RSSフィードから詳細なエピソードデータ抽出
- メタデータ、オーディオ情報取得
- エピソード詳細の包括的取得

**価格**: Apify料金プランに依存

**ポッドキャスト活用例**:
- エピソード情報のデータベース構築
- 音声ファイルURLの自動取得
- ポッドキャストアグリゲーター開発

---

### 25. Apple Podcasts Show Scraper（Apify）

**URL**: https://apify.com/scrapestorm/apple-podcasts-show-scraper---cheap/api/mcp

**機能**:
- Apple Podcastsショー情報のスクレイピング
- 番組タイトル、アーティスト、ジャンル取得
- リリース日、説明文、アートワーク取得

**価格**: Apify料金プラン（"cheap"表記あり）

**ポッドキャスト活用例**:
- ポッドキャストディレクトリの構築
- 番組情報の自動更新
- ジャンル別カタログ作成

---

## 総括：ポッドキャスト音声システム構築のための推奨構成

### 最小構成（無料）

1. **文字起こし**: Local Speech-to-Text MCP（whisper.cpp）
2. **音声合成**: Kokoro TTS MCP または Edge TTS
3. **コンテンツ収集**: YouTube Transcript Server（kimtaeyoon83）
4. **RSS管理**: MCP-RSS-Crawler または RSS Feed MCP

**総コスト**: 0円（完全無料）

---

### 高品質構成（一部有料）

1. **文字起こし**: Audio Transcriber MCP（OpenAI Whisper API）
2. **音声合成**: ElevenLabs MCP（10,000クレジット/月無料）
3. **コンテンツ収集**: Firecrawl MCP + YouTube Transcript
4. **RSS管理**: MCP-RSS-Crawler
5. **ニュース取得**: News API MCP（100リクエスト/日無料）
6. **ポッドキャストデータ**: Podcast Intelligence Aggregator（Apify）

**総コスト**:
- 無料枠内: 0円
- 超過時: OpenAI Whisper（$0.006/分）、ElevenLabs（従量課金）、Firecrawl（プラン次第）

---

### エンタープライズ構成

1. **文字起こし**: Audio Transcription Server（多エンジン）
2. **音声合成**: mcp-tts（マルチエンジン）+ ElevenLabs
3. **コンテンツ収集**: Firecrawl MCP（全機能）
4. **RSS管理**: RSS Reader MCP + MCP-RSS-Crawler
5. **ニュース取得**: News API MCP（有料プラン）
6. **ポッドキャストデータ**: 全Apifyツール
7. **YouTube**: YouTube Transcript Server + YouTube Transcribe

**総コスト**: 状況により変動（月額$100-500想定）

---

## 情報源（Sources）

### MCP.so
- [Audio Transcriber MCP](https://mcp.so/server/audio-transcriber-mcp/Ichigo3766)
- [MCP TTS Say](https://mcp.so/server/mcp-tts-say)
- [mcp-tts by blacktop](https://mcp.so/server/mcp-tts/blacktop)
- [MCP TTS Server](https://mcp.so/server/MCP_tts_server)
- [ElevenLabs MCP](https://mcp.so/server/elevenlabs-mcp/elevenlabs)
- [Local Voice MCP](https://mcp.so/server/local-voice-mcp/CodeCraftersLLC)
- [Kokoro TTS MCP](https://mcp.so/server/kokoro-tts-mcp/mberg)
- [Local STT MCP](https://mcp.so/server/local-stt-mcp/SmartLittleApps)
- [MCP-RSS-Crawler](https://mcp.so/server/mcp-rss-crawler)
- [News API MCP](https://mcp.so/server/news_mcp/kcjonnyc)
- [Firecrawl MCP Server](https://mcp.so/server/firecrawl-mcp-server)

### Smithery.ai
- [YouTube Transcript Server](https://smithery.ai/server/@sinco-lab/mcp-youtube-transcript)
- [YouTube Transcript Extractor](https://smithery.ai/server/@alfie-max/youtube-mcp)

### mcpmarket.com
- [Edge TTS](https://mcpmarket.com/server/edge-tts)
- [Audio Transcriber](https://mcpmarket.com/server/audio-transcriber)
- [TTS Server](https://mcpmarket.com/server/tts-server)
- [Kokoro TTS](https://mcpmarket.com/server/kokoro-tts)
- [YouTube Transcribe](https://mcpmarket.com/server/youtube-transcribe)

### GitHub
- [kimtaeyoon83/mcp-server-youtube-transcript](https://github.com/kimtaeyoon83/mcp-server-youtube-transcript)
- [jkawamoto/mcp-youtube-transcript](https://github.com/jkawamoto/mcp-youtube-transcript)
- [Ichigo3766/audio-transcriber-mcp](https://github.com/Ichigo3766/audio-transcriber-mcp)
- [mberg/kokoro-tts-mcp](https://github.com/mberg/kokoro-tts-mcp)
- [elevenlabs/elevenlabs-mcp](https://github.com/elevenlabs/elevenlabs-mcp)
- [CodeCraftersLLC/local-voice-mcp](https://github.com/CodeCraftersLLC/local-voice-mcp)
- [kwp-lab/rss-reader-mcp](https://github.com/kwp-lab/rss-reader-mcp)

### Apify MCP Servers
- [Podcast Intelligence Aggregator](https://apify.com/benthepythondev/podcast-intelligence-aggregator/api/mcp)
- [Podcast API](https://apify.com/vivid_astronaut/podcast/api/mcp)
- [Podcast Episode Extractor](https://apify.com/simplifysme/podcast-episode-extractor/api/mcp)
- [Apple Podcasts Show Scraper](https://apify.com/scrapestorm/apple-podcasts-show-scraper---cheap/api/mcp)

### その他
- [Feed MCP - Awesome MCP Servers](https://mcpservers.org/servers/richardwooding/feed-mcp)
- [ElevenLabs Blog - MCP Launch](https://elevenlabs.io/blog/introducing-elevenlabs-mcp)
- [OpenAI Text-to-Speech API](https://platform.openai.com/docs/guides/text-to-speech)
- [PulseMCP - Audio Transcriber](https://www.pulsemcp.com/servers/audio-transcriber)

---

**調査完了**: 2026年2月11日
**調査対象**: MCP.so、Smithery.ai、mcpmarket.com
**実在確認済み**: 全ツール
