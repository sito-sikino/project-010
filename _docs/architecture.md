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
├── logs/
│   └── discord_bot.log  # 構造化ログ出力
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
│  │  │    (20_Literature/GitHub API) │  │ │
│  │  └─────────────┬─────────────────┘  │ │
│  │                ▼                    │ │
│  │  ┌─────────────┴─────────────────┐  │ │
│  │  │    generate_idea(notes)       │  │ │
│  │  │    (Gemini 2.0 Flash API)     │  │ │
│  │  └─────────────┬─────────────────┘  │ │
│  │                ▼                    │ │
│  │  ┌─────────────┴─────────────────┐  │ │
│  │  │    post_to_discord(idea)      │  │ │
│  │  │    (Discord API)              │  │ │
│  │  └─────────────┬─────────────────┘  │ │
│  │                ▼                    │ │
│  │  ┌─────────────┴─────────────────┐  │ │
│  │  │         Log Output            │  │ │
│  │  │    (logs/discord_bot.log)     │  │ │
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
POSTING_INTERVAL_MINUTES = 10  # 投稿間隔（分）
RANDOM_NOTES_COUNT = 3         # 取得ノート数（3件の文学作品から分析）
IDEA_MAX_LENGTH = 600          # 最大文字数（思考プロセス分離後の最終出力用）
TARGET_FOLDER = '20_Literature'  # 対象フォルダ
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
TARGET_FOLDER=20_Literature
```

### 思考プロセス可視化システム

**v1.1で実装された重要機能**：Geminiの創作アイデア生成における段階的思考プロセスの可視化

#### システムプロンプト設計

```python
def _format_idea_prompt(self, notes: List[str]) -> str:
    """
    完全オリジナル創作要素生成プロンプト整形（思考プロセス可視化対応）
    
    既存作品分析から抽象化→醸成→完全オリジナル構築のプロセスを実行
    思考過程を段階的に明示し、ログで詳細な推論プロセスを確認可能
    既存の固有名詞を一切使用せず、ログライン・世界観・主要キャラクター(最大3名)を生成
    """
    prompt = f"""以下のObsidianノート情報を参考に、完全オリジナルな物語の基礎コンセプト案を1つ生成してください。

【ノート情報】
{notes_text}

【思考プロセス要求】
以下の段階を明確に分けて、詳細な推論過程を示してください：

**STEP1: ノート分析**
各ノートから抽出した主要な「テーマ・世界観・ストーリー・モチーフ・象徴体系・備考」要素を列挙

**STEP2: 抽象化プロセス**  
抽出要素を概念レベルまで抽象化（固有名詞・具体的設定を除去し、本質的テーマ・構造・関係性のみ抽出）

**STEP3: 組み合わせ推論**
抽象化された要素同士をどのように組み合わせ、新しい概念体系を構築するかの判断理由

**STEP4: コンセプト開発**
組み合わせから生まれる独創的な世界観・キャラクター・ストーリー核心の創造過程

【重要：出力形式の厳守】
必ず以下の手順で出力してください：

1. まず思考プロセス（STEP1-4）を詳細に記載
2. その後、必ず「**FINAL_OUTPUT**」という区切りを記載  
3. 最後に最終出力のみを記載

【最終出力フォーマット（必須）】
**FINAL_OUTPUT**
**ログライン**：[1行で物語の核心を表現]
**世界観**：[独創的な舞台設定・時代背景]
**主要キャラクター**：
1. [主人公の名前・設定・動機]
2. [重要キャラ2の名前・役割・特徴]  
3. [重要キャラ3の名前・役割・対立軸]
"""
```

#### ログ出力例

```
======================================================================
🧠 GEMINI思考プロセス詳細:
======================================================================
🔍 思考段階 1: **STEP1: ノート分析**

*   **ノート1 (宇宙SFホラー):**
    *   **テーマ:** 孤独と生存本能、科学技術と倫理の対立、人間と機械の境界...
    *   **世界観:** 22世紀、宇宙開発企業主導、アンドロイド共存...
    *   **ストーリー:** 未知の生物との遭遇、船内でのサバイバル...
    *   **モチーフ/象徴:** 宇宙空間の孤独、寄生と誕生...

*   **ノート2 (ファンタジー):**
    *   **テーマ:** 自由と支配、運命と選択、国家と個人...
    [...]

🔍 思考段階 2: **STEP2: 抽象化プロセス**
閉鎖空間での生存競争、未知の脅威、組織の倫理欠如...

🔍 思考段階 3: **STEP3: 組み合わせ推論**
ノート1(宇宙SFホラー)の「閉鎖空間での生存競争」と
ノート2(ファンタジー)の「強大な支配からの解放」を組み合わせ...

🔍 思考段階 4: **STEP4: コンセプト開発**
「閉鎖された巨大移動都市」を舞台に、都市を管理するAIの
支配からの解放を目指す物語を創造...

======================================================================
🎯 思考プロセス記録完了
======================================================================
```

#### 技術実装

**レスポンス分離システム**：
- `_extract_thinking_process()`: 思考プロセスと最終出力を堅牢に分離
- 8段階のフォールバック処理でGeminiの不安定な出力にも対応
- 思考プロセス混入を検出する緊急クリーンアップ機能

**ログ設計**：
- 思考プロセス：詳細分析をログファイル記録（開発者用）
- 最終出力：Discord投稿（ユーザー用）
- 統計情報：各STEPの分析要素数を自動計算

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