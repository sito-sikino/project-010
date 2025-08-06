"""
Discord投稿機能テスト

生成アイデアの指定チャンネル投稿機能テスト
Red → Green → Refactor → Commit サイクル
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os


class TestDiscordPost:
    """Discord投稿機能テスト"""

    @pytest.mark.asyncio
    async def test_post_to_discord(self):
        """Discord投稿テスト (モック使用)"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo',
            'DISCORD_CHANNEL_ID': '123456789012345678'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # テスト用アイデア
            test_idea = "時間を操る魔法使いが、古代ドラゴンと共に森の秘密を解き明かす壮大な冒険。主人公は時計の力で過去と現在を行き来し、失われた魔法の真実に迫る。"
            
            # Discordチャンネルをモック化
            mock_channel = AsyncMock()
            mock_channel.send = AsyncMock(return_value=MagicMock())
            
            # get_channelをモック化
            with patch.object(bot, 'get_channel', return_value=mock_channel):
                # Discord投稿実行
                await bot.post_to_discord(test_idea)
                
                # 投稿メソッドが呼ばれたことを確認
                mock_channel.send.assert_called_once()
                
                # 送信されたメッセージにアイデアが含まれることを確認
                sent_message = mock_channel.send.call_args[0][0]
                assert test_idea in sent_message

    def test_message_formatting(self):
        """メッセージフォーマットテスト"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo',
            'DISCORD_CHANNEL_ID': '123456789012345678'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            test_idea = "魔法の森でドラゴンが目覚める物語"
            
            # メッセージフォーマット機能が存在することを確認
            assert hasattr(bot, '_format_discord_message')
            
            # フォーマット実行
            formatted_message = bot._format_discord_message(test_idea)
            
            # フォーマット結果の基本検証
            assert isinstance(formatted_message, str)
            assert len(formatted_message) > 0
            assert test_idea in formatted_message
            
            # Discord 2000文字制限以内であることを確認
            assert len(formatted_message) <= 2000

    @pytest.mark.asyncio
    async def test_long_message_handling(self):
        """長文メッセージ処理テスト"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo',
            'DISCORD_CHANNEL_ID': '123456789012345678'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # 2000文字を超える長いアイデア
            long_idea = "非常に長い物語のアイデア。" * 200  # 2400文字程度
            
            # Discordチャンネルをモック化
            mock_channel = AsyncMock()
            mock_channel.send = AsyncMock(return_value=MagicMock())
            
            with patch.object(bot, 'get_channel', return_value=mock_channel):
                # 長文投稿実行
                await bot.post_to_discord(long_idea)
                
                # 投稿が実行されることを確認
                mock_channel.send.assert_called_once()
                
                # 送信メッセージが2000文字以内に制限されることを確認
                sent_message = mock_channel.send.call_args[0][0]
                assert len(sent_message) <= 2000

    @pytest.mark.asyncio
    async def test_post_error_handling(self):
        """投稿エラーハンドリングテスト"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo',
            'DISCORD_CHANNEL_ID': '123456789012345678'
        }, clear=False):
            from main import DiscordIdeaBot, DiscordAPIError
            
            bot = DiscordIdeaBot()
            
            test_idea = "テストアイデア"
            
            # チャンネル取得エラーをシミュレート
            with patch.object(bot, 'get_channel', return_value=None):
                # Discord API例外が発生することを確認
                with pytest.raises(DiscordAPIError) as exc_info:
                    await bot.post_to_discord(test_idea)
                
                # エラーメッセージにチャンネル関連情報が含まれることを確認
                assert "channel" in str(exc_info.value).lower() or \
                       "discord" in str(exc_info.value).lower()