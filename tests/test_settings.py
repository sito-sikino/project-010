"""
設定管理テスト

Red → Green → Refactor → Commit サイクルのテストファースト実装
"""

import pytest
import os
from unittest.mock import patch


class TestSettings:
    """設定管理の基本機能テスト"""

    def test_load_env_variables(self):
        """環境変数読み込みテスト"""
        # .env ファイル読み込み機能のテスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            # settingsモジュールをリロードして環境変数が正しく読み込まれることを確認
            import importlib
            import sys
            if 'settings' in sys.modules:
                del sys.modules['settings']
            settings = importlib.import_module('settings')
            
            assert settings.GITHUB_TOKEN == 'test_github_token'
            assert settings.GEMINI_API_KEY == 'test_gemini_key' 
            assert settings.DISCORD_BOT_TOKEN == 'test_discord_token'

    def test_required_settings_exist(self):
        """必須設定値存在テスト"""
        # 必須の設定値がすべて定義されていることを確認
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token',
            'GEMINI_API_KEY': 'test_key',
            'DISCORD_BOT_TOKEN': 'test_bot_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            import importlib
            import sys
            if 'settings' in sys.modules:
                del sys.modules['settings']
            settings = importlib.import_module('settings')
        
            # 必須項目がNoneでないことを確認
            assert settings.GITHUB_TOKEN is not None
            assert settings.GEMINI_API_KEY is not None
            assert settings.DISCORD_BOT_TOKEN is not None
            assert settings.OBSIDIAN_REPO_OWNER is not None
            assert settings.OBSIDIAN_REPO_NAME is not None
            assert settings.POSTING_INTERVAL is not None
            assert settings.RANDOM_NOTES_COUNT is not None

    def test_fail_fast_on_missing_env(self):
        """環境変数未設定時のFail-Fast例外処理テスト"""
        # 重要な環境変数が未設定の場合、起動時に例外が発生することを確認
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception) as exc_info:
                # settings.py のインポート時に例外が発生することを期待
                import importlib
                import sys
                if 'settings' in sys.modules:
                    del sys.modules['settings']
                importlib.import_module('settings')
            
            # 例外メッセージに環境変数関連のエラーが含まれることを確認
            assert 'environment variable' in str(exc_info.value).lower() or \
                   'env' in str(exc_info.value).lower() or \
                   'required' in str(exc_info.value).lower()