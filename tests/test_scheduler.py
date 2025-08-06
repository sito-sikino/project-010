"""
スケジューラー統合機能テスト

GitHub→Gemini→Discord統合フローの10分間隔自動実行テスト  
Red → Green → Refactor → Commit サイクル
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os


class TestScheduler:
    """スケジューラー統合機能テスト"""

    @pytest.mark.asyncio
    async def test_scheduled_task_setup(self):
        """スケジュールタスク設定テスト"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo',
            'DISCORD_CHANNEL_ID': '123456789012345678'
        }, clear=False):
            from main import DiscordIdeaBot
            from settings import POSTING_INTERVAL_MINUTES
            
            bot = DiscordIdeaBot()
            
            # スケジュールタスクメソッドの存在確認
            assert hasattr(bot, 'generate_and_post_idea')
            
            # タスクの設定確認
            task = bot.generate_and_post_idea
            assert task is not None
            
            # 間隔設定確認 (10分)
            assert task.minutes == POSTING_INTERVAL_MINUTES
            
            # タスクが開始可能状態であることを確認
            assert hasattr(task, 'start')
            assert hasattr(task, 'stop')

    @pytest.mark.asyncio
    async def test_main_workflow(self):
        """統合フローテスト (GitHub→Gemini→Discord)"""
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
            
            # 各段階をモック化
            test_notes = ["テストノート1", "テストノート2"]
            test_titles = ["note1.md", "note2.md"]
            test_idea = "生成されたテストアイデア"
            
            # GitHub API モック
            with patch.object(bot, 'get_random_notes', new_callable=AsyncMock) as mock_get_notes:
                mock_get_notes.return_value = (test_notes, test_titles)
                
                # Gemini API モック  
                with patch.object(bot, 'generate_idea', new_callable=AsyncMock) as mock_generate:
                    mock_generate.return_value = test_idea
                    
                    # Discord API モック
                    with patch.object(bot, 'post_to_discord', new_callable=AsyncMock) as mock_post:
                        # 統合フロー実行
                        await bot.generate_and_post_idea()
                        
                        # 各段階が正しい順序で呼ばれることを確認
                        mock_get_notes.assert_called_once()
                        mock_generate.assert_called_once_with(test_notes, test_titles)
                        mock_post.assert_called_once_with(test_idea)

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """統合フロー例外処理テスト"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo',
            'DISCORD_CHANNEL_ID': '123456789012345678'
        }, clear=False):
            from main import DiscordIdeaBot, GitHubAPIError
            
            bot = DiscordIdeaBot()
            
            # GitHub API エラーをシミュレート
            with patch.object(bot, 'get_random_notes', new_callable=AsyncMock) as mock_get_notes:
                mock_get_notes.side_effect = GitHubAPIError("GitHub API test error")
                
                # Fail-Fast により GitHubAPIError が伝播することを確認
                with pytest.raises(GitHubAPIError) as exc_info:
                    await bot.generate_and_post_idea()
                
                # エラーメッセージ確認
                assert "GitHub API test error" in str(exc_info.value)
                
                # GitHub API 呼び出し確認
                mock_get_notes.assert_called_once()

    def test_timing_verification(self):
        """タスクタイミング設定確認テスト"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo',
            'DISCORD_CHANNEL_ID': '123456789012345678'
        }, clear=False):
            from main import DiscordIdeaBot
            from settings import POSTING_INTERVAL_MINUTES
            
            bot = DiscordIdeaBot()
            
            # スケジュールタスクの間隔設定確認
            task = bot.generate_and_post_idea
            
            # 10分設定の確認
            assert task.minutes == POSTING_INTERVAL_MINUTES
            
            # タスクの基本設定確認
            assert not task.is_running()  # 初期状態では停止
            assert task.current_loop == 0  # 実行回数は0