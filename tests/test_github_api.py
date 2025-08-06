"""
GitHub API連携テスト

ObsidianリポジトリからランダムMarkdownファイル取得機能テスト
Red → Green → Refactor → Commit サイクル
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os
from github import Github


class TestGitHubAPI:
    """GitHub API連携機能テスト"""

    def test_github_client_initialization(self):
        """PyGithub初期化テスト"""
        # GitHub クライアント初期化テスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # GitHub クライアントが初期化されていることを確認
            assert hasattr(bot, 'github_client')
            assert bot.github_client is not None
            
            # リポジトリ設定が正しいことを確認
            assert hasattr(bot, 'repo_owner')
            assert hasattr(bot, 'repo_name')
            assert bot.repo_owner == 'test_owner'
            assert bot.repo_name == 'test_repo'

    @pytest.mark.asyncio
    async def test_get_random_notes(self):
        """ランダムノート取得テスト (モック使用)"""
        # ランダムMarkdownファイル取得のモックテスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # GitHub APIレスポンスをモック化
            mock_file1 = MagicMock()
            mock_file1.name = 'note1.md'
            mock_file1.type = 'file'
            mock_file1.size = 1000  # 1KB
            mock_file1.decoded_content.decode.return_value = '# Note 1\nContent of note 1'
            
            mock_file2 = MagicMock()  
            mock_file2.name = 'note2.md'
            mock_file2.type = 'file'
            mock_file2.size = 2000  # 2KB
            mock_file2.decoded_content.decode.return_value = '# Note 2\nContent of note 2'
            
            mock_file3 = MagicMock()
            mock_file3.name = 'not_markdown.txt'
            mock_file3.type = 'file'
            
            mock_dir = MagicMock()
            mock_dir.type = 'dir'
            
            mock_repo = MagicMock()
            mock_repo.get_contents.return_value = [mock_file1, mock_file2, mock_file3, mock_dir]
            
            with patch.object(bot.github_client, 'get_repo', return_value=mock_repo):
                # ランダムノート取得実行
                notes = await bot.get_random_notes()
                
                # 結果検証
                assert isinstance(notes, list)
                assert len(notes) > 0
                # Markdownファイルのみが含まれることを確認
                for note in notes:
                    assert isinstance(note, str)
                    assert len(note) > 0

    def test_markdown_file_filtering(self):
        """.mdファイルフィルタリングテスト"""
        # Markdownファイルフィルタリング機能のテスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # テスト用ファイルリスト
            mock_files = []
            
            mock_file1 = MagicMock()
            mock_file1.name = 'note1.md'
            mock_file1.type = 'file'
            mock_files.append(mock_file1)
            
            mock_file2 = MagicMock()
            mock_file2.name = 'note2.markdown'
            mock_file2.type = 'file'
            mock_files.append(mock_file2)
            
            mock_file3 = MagicMock()
            mock_file3.name = 'document.txt'
            mock_file3.type = 'file'
            mock_files.append(mock_file3)
            
            mock_file4 = MagicMock()
            mock_file4.name = 'image.png'
            mock_file4.type = 'file'
            mock_files.append(mock_file4)
            
            mock_file5 = MagicMock()
            mock_file5.name = 'config.json'
            mock_file5.type = 'file'
            mock_files.append(mock_file5)
            
            mock_folder = MagicMock()
            mock_folder.name = 'folder'
            mock_folder.type = 'dir'
            mock_files.append(mock_folder)
            
            # Markdownファイルフィルタリングメソッドが存在することを確認
            assert hasattr(bot, '_filter_markdown_files')
            
            # フィルタリング実行
            markdown_files = bot._filter_markdown_files(mock_files)
            
            # .mdファイルのみが抽出されることを確認
            assert len(markdown_files) == 2  # note1.md と note2.markdown
            assert all(f.name.endswith(('.md', '.markdown')) for f in markdown_files)
            assert all(f.type == 'file' for f in markdown_files)