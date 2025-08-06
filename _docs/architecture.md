# Discord LLM Bot - アーキテクチャ設計

## 採用アーキテクチャ: パターン1（シンプル・モノリス）

### 概要

シンプルで理解しやすい単一ファイル構造により、最速の初期実装と最小の学習コストを実現。MVP での早期運用検証に最適な構造。

### ファイル構成

```
project-010/
├── main.py              # 全機能統合（Bot + API）
├── settings.py          # 設定管理（一元化）
├── .env                 # 環境変数（API キー等）
├── requirements.txt     # 依存関係
└── tests/
    └── test_main.py     # ユニットテスト
```

### アーキテクチャ図

```
┌─────────────────────────────────────────┐
│              main.py                    │
│  ┌─────────────────────────────────────┐ │
│  │         DiscordIdeaBot              │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │    @tasks.loop(minutes=10)      │ │ │
│  │  │  generate_and_post_idea()       │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │                │                    │ │
│  │  ┌─────────────▼─────────────────┐  │ │
│  │  │    get_random_notes()         │  │ │ 
│  │  │    (GitHub API)               │  │ │
│  │  └─────────────┬─────────────────┘  │ │
│  │                ▼                    │ │
│  │  ┌─────────────┴─────────────────┐  │ │
│  │  │    generate_idea(notes)       │  │ │
│  │  │    (Gemini API)               │  │ │
│  │  └─────────────┬─────────────────┘  │ │
│  │                ▼                    │ │
│  │  ┌─────────────┴─────────────────┐  │ │
│  │  │    post_to_discord(idea)      │  │ │
│  │  │    (Discord API)              │  │ │
│  │  └───────────────────────────────┘  │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### コア実装設計

```python
class DiscordIdeaBot(commands.Bot):
    def __init__(self):
        """Bot初期化"""
        super().__init__(command_prefix='!', intents=discord.Intents.default())
        # GitHub、Geminiクライアント初期化
        self.github_client = Github(GITHUB_TOKEN)
        self.gemini_client = genai.Client()
        
    @tasks.loop(minutes=10)
    async def generate_and_post_idea(self):
        """メインループ：アイデア生成・投稿"""
        try:
            # 1. GitHubからランダムノート取得
            notes = await self.get_random_notes()
            
            # 2. Geminiでアイデア生成
            idea = await self.generate_idea(notes)
            
            # 3. Discordに投稿
            await self.post_to_discord(idea)
            
        except Exception as e:
            # Fail-Fast: 例外時は即停止
            self.logger.error(f"処理失敗: {e}")
            raise
    
    async def get_random_notes(self) -> List[str]:
        """GitHub API経由でランダムObsidianノート取得"""
        pass
        
    async def generate_idea(self, notes: List[str]) -> str:
        """Gemini API経由でアイデア生成"""
        pass
        
    async def post_to_discord(self, idea: str):
        """Discord API経由で投稿"""
        pass
```

### 技術スタック

| 技術 | 選定理由 |
|------------|------------------|
| **discord.py** | Discord Bot実装の標準ライブラリ、定期実行のtasks拡張 |
| **PyGithub** | GitHub API統合、ランダムファイル取得に最適 |
| **google-genai** | Gemini 2.0 Flash API公式SDK |
| **python-dotenv** | 環境変数管理、設定分離 |

### API制限管理

```python
# API制限遵守
GEMINI_API_LIMIT = 200  # req/day
GITHUB_API_LIMIT = 5000 # req/hour

# 実際の使用量（10分間隔）
DAILY_REQUESTS_GEMINI = 144   # 200req/day以内（余裕あり）
DAILY_REQUESTS_GITHUB = 144   # 5000req/hour以内（余裕あり）
```

### 設定管理方針

**settings.py: 意味的な設定値**
```python
# アイデア生成設定
IDEA_GENERATION_INTERVAL = 10  # 分
RANDOM_NOTES_COUNT = 5         # 取得ノート数
IDEA_MAX_LENGTH = 500          # 最大文字数
```

**.env: 機密情報・環境依存値**
```python
# API認証情報
GITHUB_TOKEN=ghp_xxxxx
GEMINI_API_KEY=xxxxx
DISCORD_BOT_TOKEN=xxxxx

# リポジトリ設定
OBSIDIAN_REPO_OWNER=username
OBSIDIAN_REPO_NAME=vault
```

### エラーハンドリング（Fail-Fast原則）

```python
class BotError(Exception):
    """Bot基底例外"""

class GitHubAPIError(BotError):
    """GitHub API例外"""

class GeminiAPIError(BotError):
    """Gemini API例外"""

class DiscordAPIError(BotError):
    """Discord API例外"""

# 例外時は即停止、フォールバックなし
```

### テスト戦略

```python
# test_main.py
class TestDiscordIdeaBot:
    def test_get_random_notes(self):
        """GitHub APIノート取得テスト"""
        
    def test_generate_idea(self):
        """Gemini APIアイデア生成テスト"""
        
    def test_post_to_discord(self):
        """Discord投稿テスト"""
        
    def test_full_workflow(self):
        """統合テスト"""
```

### デプロイメント

```bash
# VPS上での実行
python main.py

# 24時間運用
# systemdサービス登録推奨
```

### メリット・デメリット

**メリット**
- ✅ 最速初期実装（1日以内）
- ✅ 最小学習コスト
- ✅ シンプルなデプロイ・運用
- ✅ MVP に最適

**デメリット**
- ⚠️ 大規模拡張時のリファクタコスト
- ⚠️ ユニットテストの部分的制約
- ⚠️ 責任境界の曖昧さ

**拡張時の移行戦略**
将来の拡張要件に応じて、段階的に3層構造へリファクタリング。

### 開発フェーズとの対応

本アーキテクチャは CLAUDE.md で定義された開発プロセスに完全準拠：

- **Phase 1 EXPLORE**: 完了（API仕様調査済み）
- **Phase 2 PLAN**: todo.md でマイクロタスク分割
- **Phase 3 IMPLEMENT**: TDD サイクルで段階実装
- **Phase 4 VERIFY**: 統合テスト・品質検証