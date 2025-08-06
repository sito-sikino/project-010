# Discord LLM Bot - 要件定義書

## 1. プロジェクト概要

GitHub上のObsidian Vaultからランダムにノートを取得し、Gemini 2.0 Flashがそれらを組み合わせてアイデア自動生成・投稿するDiscordボット。最小限の構成で24時間VPS稼働で運用する。

## 2. 機能要件

### 2.1 アイデア生成・投稿（10分間隔）
- **ランダムノート取得**: GitHub API経由でObsidian Vault特定フォルダ（20_Literature）からランダムに複数ノートを取得
- **アイデア生成**: 取得したノート断片をGemini 2.0 Flashに渡して創作アイデア（物語の基礎コンセプト案）生成
- **自動投稿**: 生成されたアイデアをDiscordに投稿
- **ログ記録**: 全処理過程をファイル出力で永続記録

## 3. 技術要件

### 3.1 API制限遵守
```
Gemini 2.0 Flash: 200 req/day上限
└── アイデア生成・投稿: 144回/日 (10分間隔で十分な余裕)

GitHub API: 5,000 req/hour上限
└── ランダムノート取得: 144回/日 (十分な余裕)
```

### 3.2 処理フロー
```
アイデア生成（10分間隔）
GitHub API → 20_Literatureフォルダからランダムノート取得 → Gemini生成 → Discord投稿
     ↓              ↓                    ↓           ↓
  ログ記録      ファイル名記録        コンセプト記録   投稿結果記録
```

### 3.3 アーキテクチャパターン
**シンプルなスケジューラー**

```
Main Scheduler (10min間隔)
└── Content Generation Function
    ├── GitHub API: 20_Literatureフォルダからランダムノート取得
    ├── Gemini 2.0 Flash: 物語基礎コンセプト案生成
    ├── Discord API: 投稿
    └── Log System: ファイル出力記録
```

## 4. 非機能要件

### 4.1 稼働要件
- **稼働環境**: VPS上での24時間常時稼働
- **可用性**: Fail-Fast原則による即時障害検知・停止
- **回復性**: エラー発生時の自動再起動

### 4.2 性能要件
- **処理能力**: API制限内での最大スループット
- **応答速度**: 投稿処理の安定実行
- **メモリ使用**: 最小限（データ永続化なし）

### 4.3 セキュリティ要件
- **認証情報**: `.env`による環境変数管理
- **API Key**: GitHub、Gemini、Discord APIキー管理
- **ログ管理**: 機密情報の非記録、構造化ログのファイル出力（logs/discord_bot.log）

## 5. 開発制約

### 5.1 設定管理原則
- **一元管理**: `settings.py`での意味的設定値管理
- **環境分離**: `.env`での機密情報・環境依存値管理
- **ハードコード禁止**: 具体値の直接記述禁止

### 5.2 開発手法
- **TDD採用**: Red→Green→Refactor→Commitサイクル
- **Fail-Fast**: 異常時の即時停止、フォールバック禁止
- **最小実装**: 要求機能のみの実装

### 5.3 品質基準
- **コード品質**: `black`, `flake8`, `mypy`準拠
- **テスト**: `pytest`による単体・統合テスト
- **文書化**: 日本語コメントによる意図説明

## 6. 技術スタック

- **言語**: Python 3.9+
- **フレームワーク**: discord.py
- **API**: GitHub API, Google Gemini 2.0 Flash, Discord API
- **稼働環境**: VPS (Linux)
- **スケジューラー**: APScheduler または asyncio

## 7. 開発フェーズ

```
Phase 1: EXPLORE（調査）
├── GitHub API仕様調査
├── Gemini 2.0 Flash API仕様調査
└── Discord Bot実装方法調査

Phase 2: PLAN（計画）
├── タスク分割（todo.md）
├── TDDサイクル設計
└── 設定値定義

Phase 3: IMPLEMENT（実装）
├── Red: 失敗テスト作成
├── Green: 最小実装
├── Refactor: 品質改善
└── Commit: 履歴化

Phase 4: VERIFY（統合検証）
├── 統合テスト実行
├── 品質基準確認
└── 成果物固定
```