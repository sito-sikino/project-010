"""
Discord Bot基盤テスト

Discord接続・認証の基本機能テスト
Red → Green → Refactor → Commit サイクル
"""

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import os


class TestDiscordBot:
    """Discord Bot基本機能テスト"""

    def test_bot_initialization(self):
        """Bot初期化テスト"""
        # Discord Bot の基本初期化テスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            # main.py から DiscordIdeaBot をインポート
            from main import DiscordIdeaBot
            
            # Botインスタンス作成
            bot = DiscordIdeaBot()
            
            # 基本設定確認
            assert bot is not None
            assert isinstance(bot, discord.ext.commands.Bot)
            assert bot.command_prefix == '!'
            
    @pytest.mark.asyncio
    async def test_discord_connection(self):
        """Discord接続テスト (モック使用)"""
        # Discord API接続のモックテスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key', 
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            # Discord接続をモック化
            with patch.object(discord.Client, 'login', new_callable=AsyncMock) as mock_login:
                mock_login.return_value = None
                
                bot = DiscordIdeaBot()
                
                # 接続テスト実行
                await bot.login('test_token')
                
                # 接続メソッドが呼ばれたことを確認
                mock_login.assert_called_once_with('test_token')

    @pytest.mark.asyncio  
    async def test_on_ready_event(self):
        """Bot起動完了イベントテスト"""
        # Bot起動時のon_readyイベント処理テスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token', 
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # on_ready イベント処理が存在することを確認
            assert hasattr(bot, 'on_ready')
            assert callable(getattr(bot, 'on_ready'))
            
            # on_ready を呼び出してもエラーが発生しないことを確認
            await bot.on_ready()