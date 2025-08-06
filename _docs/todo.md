# Discord LLM Bot - 詳細実装計画

## Phase 3: IMPLEMENT - マイクロタスクチェックリスト

> **開発原則**: TDD徹底 (Red→Green→Refactor→Commit) | Fail-Fast | venv必須 | 設定一元化

---

### 🔧 タスク1: 開発環境構築
**目標**: Python開発環境とプロジェクト基盤の整備

#### チェックリスト:
- [ ] `python -m venv venv` で仮想環境作成・有効化確認
- [ ] `pip install -r requirements.txt` で依存ライブラリインストール成功
- [ ] `.env.example` ファイル作成 (API Keys テンプレート含む)
- [ ] `.gitignore` ファイル作成 (`.env`, `__pycache__`, `venv/` 除外)
- [ ] `tests/` ディレクトリ作成確認

**受け入れ条件**:
- ✅ venv環境でPythonライブラリが正常インストール済み
- ✅ `.env.example` から `.env` にコピーして環境変数設定可能
- ✅ Git管理から機密情報が除外済み

---

### ⚙️ タスク2: 設定管理基盤実装
**目標**: settings.py + .env による設定一元化
**TDDサイクル**: Red → Green → Refactor → Commit

#### チェックリスト:
- [ ] **Red**: `tests/test_settings.py` でテスト作成 (失敗状態)
  - [ ] `test_load_env_variables()` - 環境変数読み込みテスト
  - [ ] `test_required_settings_exist()` - 必須設定値存在テスト
- [ ] **Green**: `settings.py` 最小実装
  - [ ] `python-dotenv` で `.env` ファイル読み込み
  - [ ] API認証情報 (GITHUB_TOKEN, GEMINI_API_KEY, DISCORD_BOT_TOKEN)
  - [ ] リポジトリ設定 (OBSIDIAN_REPO_OWNER, OBSIDIAN_REPO_NAME)
  - [ ] アイデア生成設定 (POSTING_INTERVAL, RANDOM_NOTES_COUNT)
- [ ] **Refactor**: コード品質向上
  - [ ] 型ヒント追加 (`from typing import Optional`)
  - [ ] docstring追加 (設定の意味説明)
  - [ ] 環境変数未設定時の Fail-Fast 例外処理
- [ ] **Commit**: Git コミット + dev-log作成
  - [ ] `_docs/dev-log/2025-01-XX_settings.md` 作成
  - [ ] 設定管理の設計意図・注意点記録

**受け入れ条件**:
- ✅ `pytest tests/test_settings.py` が全て合格
- ✅ `from settings import GITHUB_TOKEN` で環境変数取得成功
- ✅ 必須環境変数未設定時は起動時に Fail-Fast で停止

---

### 🤖 タスク3: Discord Bot基盤実装  
**目標**: Discord接続・認証の基本機能
**TDDサイクル**: Red → Green → Refactor → Commit

#### チェックリスト:
- [ ] **Red**: `tests/test_discord_bot.py` でテスト作成 (失敗状態)
  - [ ] `test_bot_initialization()` - Bot初期化テスト
  - [ ] `test_discord_connection()` - Discord接続テスト (モック使用)
- [ ] **Green**: `main.py` に DiscordIdeaBot クラス最小実装
  - [ ] `discord.py` の `commands.Bot` 継承
  - [ ] `__init__()` メソッドで基本設定 (prefix, intents)
  - [ ] Discord Bot Token での認証・接続確認
  - [ ] `@bot.event async def on_ready()` で起動ログ出力
- [ ] **Refactor**: エラーハンドリング追加
  - [ ] カスタム例外 `DiscordAPIError` 定義
  - [ ] 接続失敗時の Fail-Fast 例外発生
  - [ ] 構造化ログ出力 (`logging` モジュール使用)
- [ ] **Commit**: Git コミット + dev-log作成
  - [ ] `_docs/dev-log/2025-01-XX_discord_bot.md` 作成

**受け入れ条件**:
- ✅ `pytest tests/test_discord_bot.py` が全て合格
- ✅ `python main.py` でBot起動・Discord接続成功を確認
- ✅ Discord側でBotがオンライン状態で表示される

---

### 📁 タスク4: GitHub API連携実装
**目標**: ObsidianリポジトリからランダムMarkdownファイル取得
**TDDサイクル**: Red → Green → Refactor → Commit

#### チェックリスト:
- [ ] **Red**: `tests/test_github_api.py` でテスト作成 (失敗状態)
  - [ ] `test_github_client_initialization()` - PyGithub初期化テスト
  - [ ] `test_get_random_notes()` - ランダムノート取得テスト (モック使用)
  - [ ] `test_markdown_file_filtering()` - .mdファイルフィルタリングテスト
- [ ] **Green**: GitHub API連携の最小実装
  - [ ] `github = Github(GITHUB_TOKEN)` でクライアント初期化
  - [ ] `repo = github.get_repo(f"{OWNER}/{NAME}")` でリポジトリ取得
  - [ ] `repo.get_contents("")` で全ファイル一覧取得
  - [ ] `.md` 拡張子フィルタリング
  - [ ] `random.sample()` で複数ファイルをランダム選択
  - [ ] `file.decoded_content.decode('utf-8')` でテキスト取得
- [ ] **Refactor**: エラーハンドリング・最適化
  - [ ] カスタム例外 `GitHubAPIError` 定義
  - [ ] API制限エラー処理 (RateLimitExceededException)
  - [ ] ファイルサイズ制限チェック (大きすぎるファイル除外)
  - [ ] キャッシュ機能 (同一ファイル重複取得回避)
- [ ] **Commit**: Git コミット + dev-log作成
  - [ ] `_docs/dev-log/2025-01-XX_github_api.md` 作成

**受け入れ条件**:
- ✅ `pytest tests/test_github_api.py` が全て合格
- ✅ 指定リポジトリから複数のMarkdownファイル内容を取得成功
- ✅ API制限エラー時は Fail-Fast で停止確認

---

### 🧠 タスク5: Gemini API連携実装
**目標**: ノート断片から創作アイデア生成
**TDDサイクル**: Red → Green → Refactor → Commit

#### チェックリスト:
- [ ] **Red**: `tests/test_gemini_api.py` でテスト作成 (失敗状態)
  - [ ] `test_gemini_client_initialization()` - Geminiクライアント初期化テスト
  - [ ] `test_generate_idea()` - アイデア生成テスト (モック使用)
  - [ ] `test_prompt_formatting()` - プロンプト整形テスト
- [ ] **Green**: Gemini API連携の最小実装  
  - [ ] `genai.Client()` でクライアント初期化 (環境変数 GEMINI_API_KEY)
  - [ ] プロンプトテンプレート作成 (ノート断片組み合わせ指示)
  - [ ] `client.models.generate_content()` でアイデア生成
  - [ ] レスポンステキスト抽出・整形
- [ ] **Refactor**: プロンプト最適化・エラーハンドリング
  - [ ] カスタム例外 `GeminiAPIError` 定義
  - [ ] API制限エラー処理 (ResourceExhaustedException)
  - [ ] アイデア生成プロンプトの改善 (「物語の基礎コンセプト案」特化)
  - [ ] レスポンス内容の品質チェック (最小文字数, 不適切内容フィルタ)
- [ ] **Commit**: Git コミット + dev-log作成
  - [ ] `_docs/dev-log/2025-01-XX_gemini_api.md` 作成

**受け入れ条件**:
- ✅ `pytest tests/test_gemini_api.py` が全て合格
- ✅ 複数ノート断片から創作アイデア（物語コンセプト）生成成功
- ✅ API制限エラー時は Fail-Fast で停止確認

---

### 💬 タスク6: Discord投稿機能実装
**目標**: 生成アイデアの指定チャンネル投稿
**TDDサイクル**: Red → Green → Refactor → Commit

#### チェックリスト:
- [ ] **Red**: `tests/test_discord_post.py` でテスト作成 (失敗状態)
  - [ ] `test_post_to_discord()` - Discord投稿テスト (モック使用)
  - [ ] `test_message_formatting()` - メッセージフォーマットテスト
- [ ] **Green**: Discord投稿機能の最小実装
  - [ ] `channel = bot.get_channel(CHANNEL_ID)` でチャンネル取得
  - [ ] `await channel.send(message)` でメッセージ投稿
  - [ ] 投稿成功時のログ出力
- [ ] **Refactor**: 投稿フォーマット最適化
  - [ ] アイデア投稿用テンプレート作成 (絵文字・装飾含む)
  - [ ] 文字数制限対応 (Discord 2000文字制限)
  - [ ] 投稿失敗時の Fail-Fast 例外処理
- [ ] **Commit**: Git コミット + dev-log作成
  - [ ] `_docs/dev-log/2025-01-XX_discord_post.md` 作成

**受け入れ条件**:
- ✅ `pytest tests/test_discord_post.py` が全て合格  
- ✅ 指定Discordチャンネルにアイデア投稿成功確認
- ✅ 投稿失敗時は Fail-Fast で停止確認

---

### ⏰ タスク7: スケジューラー統合実装
**目標**: 10分間隔での自動アイデア生成・投稿
**TDDサイクル**: Red → Green → Refactor → Commit

#### チェックリスト:
- [ ] **Red**: `tests/test_scheduler.py` でテスト作成 (失敗状態)
  - [ ] `test_scheduled_task_setup()` - スケジュールタスク設定テスト
  - [ ] `test_main_workflow()` - GitHub→Gemini→Discord統合フローテスト (モック使用)
- [ ] **Green**: メインループ統合実装
  - [ ] `@tasks.loop(minutes=10)` デコレータ実装
  - [ ] `async def generate_and_post_idea()` メソッド実装
    - [ ] `notes = await self.get_random_notes()` - GitHubからノート取得
    - [ ] `idea = await self.generate_idea(notes)` - Geminiでアイデア生成  
    - [ ] `await self.post_to_discord(idea)` - Discord投稿
  - [ ] `@generate_and_post_idea.before_loop` で Bot Ready待機
  - [ ] Bot起動時の自動タスク開始
- [ ] **Refactor**: ログ出力・例外処理強化
  - [ ] 各処理段階での進捗ログ出力
  - [ ] 処理時間計測・記録
  - [ ] 統合フロー全体の Fail-Fast 例外処理
- [ ] **Commit**: Git コミット + dev-log作成  
  - [ ] `_docs/dev-log/2025-01-XX_scheduler.md` 作成

**受け入れ条件**:
- ✅ `pytest tests/test_scheduler.py` が全て合格
- ✅ Bot起動後10分間隔で自動投稿が動作確認
- ✅ GitHub→Gemini→Discord の完全統合フロー成功

---

### 🚨 タスク8: エラーハンドリング強化
**目標**: Fail-Fast原則に基づく例外管理
**TDDサイクル**: Red → Green → Refactor → Commit

#### チェックリスト:
- [ ] **Red**: `tests/test_error_handling.py` でテスト作成 (失敗状態)
  - [ ] `test_custom_exceptions()` - カスタム例外クラステスト
  - [ ] `test_api_error_handling()` - 各API例外処理テスト  
  - [ ] `test_fail_fast_behavior()` - Fail-Fast動作テスト
- [ ] **Green**: 例外処理基盤実装
  - [ ] `class BotError(Exception)` 基底例外定義
  - [ ] `class GitHubAPIError(BotError)`, `class GeminiAPIError(BotError)`, `class DiscordAPIError(BotError)` 派生例外
  - [ ] 各API呼び出し箇所での try-except → Fail-Fast 例外発生  
- [ ] **Refactor**: 構造化ログ・監視強化
  - [ ] `logging.getLogger(__name__)` で構造化ログ設定
  - [ ] 例外発生時の詳細情報記録 (API名, パラメータ, エラー内容)
  - [ ] ログレベル設定 (DEBUG, INFO, ERROR)
- [ ] **Commit**: Git コミット + dev-log作成
  - [ ] `_docs/dev-log/2025-01-XX_error_handling.md` 作成

**受け入れ条件**:
- ✅ `pytest tests/test_error_handling.py` が全て合格
- ✅ 各API例外発生時に専用例外クラスで Fail-Fast 停止確認  
- ✅ ログから例外原因特定可能

---

### 🧪 タスク9: 統合テスト・品質保証  
**目標**: 全体品質確認・本番稼働準備
**検証フェーズ**: 全機能統合確認

#### チェックリスト:
- [ ] **全テスト実行・品質確認**
  - [ ] `pytest` - 全テストスイート合格確認
  - [ ] `black --check .` - コードフォーマット確認
  - [ ] `flake8 .` - リント確認 (PEP8準拠)
  - [ ] `mypy .` - 型チェック確認
- [ ] **統合動作確認**
  - [ ] 10分間隔での自動投稿動作確認 (最低3回実行)
  - [ ] GitHub APIアクセス・ランダムファイル取得確認  
  - [ ] Gemini APIアイデア生成品質確認
  - [ ] Discord投稿内容・フォーマット確認
- [ ] **制限・制約確認**
  - [ ] API使用量記録 (Gemini: 144req/day以内, GitHub: 144req/day)
  - [ ] エラー発生時の Fail-Fast 停止確認
  - [ ] ログ出力内容・品質確認
- [ ] **最終文書化**
  - [ ] `_docs/dev-log/2025-01-XX_integration_test.md` 作成
  - [ ] 動作確認結果・改善点・運用注意点記録
  - [ ] Git final commit

**受け入れ条件**:
- ✅ 全テストスイート・品質チェック合格
- ✅ 10分間隔での自動投稿が安定動作  
- ✅ API制限遵守・Fail-Fast原則準拠確認
- ✅ 24時間VPS稼働準備完了

---

## 設定管理マトリックス

| 設定項目 | settings.py | .env | 用途 |
|---------|-------------|------|------|
| 投稿間隔 | `POSTING_INTERVAL_MINUTES = 10` | - | アプリケーション設定 |
| 取得ノート数 | `RANDOM_NOTES_COUNT = 5` | - | アプリケーション設定 |
| アイデア最大文字数 | `IDEA_MAX_LENGTH = 500` | - | アプリケーション設定 |
| Discord投稿チャンネル | `DISCORD_CHANNEL_ID` | `DISCORD_CHANNEL_ID=123456` | 環境依存設定 |
| GitHub認証 | - | `GITHUB_TOKEN=ghp_xxxxx` | 機密情報 |
| Gemini認証 | - | `GEMINI_API_KEY=xxxxx` | 機密情報 |
| Discord認証 | - | `DISCORD_BOT_TOKEN=xxxxx` | 機密情報 |
| リポジトリ設定 | - | `OBSIDIAN_REPO_OWNER=username` | 環境依存設定 |
| リポジトリ名 | - | `OBSIDIAN_REPO_NAME=vault` | 環境依存設定 |

---

## 進捗管理・コミットルール

### ステータス定義:
- ✅ **完了**: 受け入れ条件達成 + テスト合格 + コミット済み + dev-log作成済み
- 🔄 **進行中**: TDDサイクル実行中 (Red/Green/Refactor段階)
- ⏸️ **保留**: 依存タスク待ち・外部要因
- ❌ **ブロック**: 技術的課題・仕様不明

### コミット時の必須作業:
1. **テスト確認**: `pytest tests/test_[function].py` 合格
2. **品質確認**: `black --check`, `flake8`, `mypy` 合格  
3. **dev-log作成**: `_docs/dev-log/2025-01-XX_[function].md` 作成
   - 完了タスク詳細
   - 実装背景・設計意図
   - 副作用・注意点
   - 関連ファイル・関数一覧
4. **Gitコミット**: `git add . && git commit -m "[function]: 実装完了"`

### Phase 4移行条件:
- 全9タスクが ✅ 完了ステータス
- 統合テスト・品質保証で全項目クリア
- 24時間稼働テスト準備完了