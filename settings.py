"""
設定管理モジュール

環境変数とアプリケーション設定を一元管理
Fail-Fast原則により、必須環境変数が未設定の場合は起動時に停止
"""

import os
from typing import Optional
from dotenv import load_dotenv

# .env ファイルを読み込み
load_dotenv()

def _get_required_env(key: str) -> str:
    """
    必須環境変数を取得
    
    Args:
        key: 環境変数名
        
    Returns:
        str: 環境変数の値
        
    Raises:
        ValueError: 環境変数が未設定の場合
    """
    value: Optional[str] = os.getenv(key)
    if not value:
        raise ValueError(f"{key} environment variable is required")
    return value

# API認証情報 (環境変数から取得、必須)
GITHUB_TOKEN: str = _get_required_env('GITHUB_TOKEN')
GEMINI_API_KEY: str = _get_required_env('GEMINI_API_KEY')
DISCORD_BOT_TOKEN: str = _get_required_env('DISCORD_BOT_TOKEN')

# リポジトリ設定 (環境変数から取得、必須)
OBSIDIAN_REPO_OWNER: str = _get_required_env('OBSIDIAN_REPO_OWNER')
OBSIDIAN_REPO_NAME: str = _get_required_env('OBSIDIAN_REPO_NAME')

# Discord設定 (環境変数から取得、オプション)
DISCORD_CHANNEL_ID: Optional[str] = os.getenv('DISCORD_CHANNEL_ID')

# アイデア生成設定 (アプリケーション設定)
POSTING_INTERVAL_MINUTES: int = 10  # 投稿間隔（分）
RANDOM_NOTES_COUNT: int = 5         # 取得するノート数
IDEA_MAX_LENGTH: int = 500          # アイデア最大文字数

# Obsidianノート取得設定 (環境変数 or デフォルト値)
TARGET_FOLDER: Optional[str] = os.getenv('TARGET_FOLDER', '20_Literature')  # 対象フォルダ