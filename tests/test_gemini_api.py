"""
Gemini API連携テスト

ノート断片から創作アイデア生成機能テスト
Red → Green → Refactor → Commit サイクル
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os


class TestGeminiAPI:
    """Gemini API連携機能テスト"""

    def test_gemini_client_initialization(self):
        """Geminiクライアント初期化テスト"""
        # Gemini クライアント初期化テスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # Gemini クライアントが初期化されていることを確認
            assert hasattr(bot, 'gemini_client')
            assert bot.gemini_client is not None

    @pytest.mark.asyncio
    async def test_generate_idea(self):
        """アイデア生成テスト (モック使用)"""
        # ノート断片からアイデア生成のモックテスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # テスト用ノート断片
            test_notes = [
                "# 魔法の森\n古代の魔法使いが住んでいた森には、不思議な光る石がある。",
                "# 時間旅行\n主人公は古い時計を見つけて、過去に戻ることができるようになった。",
                "# ドラゴンの卵\n村で発見された巨大な卵から、小さなドラゴンが孵化した。"
            ]
            
            # Gemini APIレスポンスをモック化
            mock_response = MagicMock()
            mock_response.text = "時間を操る魔法使いが、古代ドラゴンと共に森の秘密を解き明かす壮大な冒険物語。主人公は時計の力で過去と現在を行き来し、失われた魔法の真実に迫る。"
            
            with patch.object(bot.gemini_client.models, 'generate_content', return_value=mock_response):
                # アイデア生成実行
                idea = await bot.generate_idea(test_notes)
                
                # 結果検証
                assert isinstance(idea, str)
                assert len(idea) > 0
                assert "魔法" in idea or "ドラゴン" in idea or "時間" in idea

    def test_prompt_formatting(self):
        """プロンプト整形テスト"""
        # プロンプトテンプレート整形機能のテスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key', 
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # テスト用ノート断片
            test_notes = [
                "魔法の世界",
                "勇敢な騎士",
                "古代の秘密"
            ]
            
            # プロンプト整形メソッドが存在することを確認
            assert hasattr(bot, '_format_idea_prompt')
            
            # プロンプト整形実行
            formatted_prompt = bot._format_idea_prompt(test_notes)
            
            # プロンプトの基本構造確認
            assert isinstance(formatted_prompt, str)
            assert len(formatted_prompt) > 0
            # ノート内容が含まれることを確認
            assert "魔法の世界" in formatted_prompt
            assert "勇敢な騎士" in formatted_prompt  
            assert "古代の秘密" in formatted_prompt
            # アイデア生成指示が含まれることを確認
            assert ("アイデア" in formatted_prompt or 
                    "物語" in formatted_prompt or 
                    "コンセプト" in formatted_prompt)

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """API制限エラー処理テスト"""
        # Gemini API制限エラー時のFail-Fast動作テスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key',
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner', 
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot, GeminiAPIError
            
            bot = DiscordIdeaBot()
            
            test_notes = ["テストノート"]
            
            # API エラーをシミュレート
            with patch.object(bot.gemini_client.models, 'generate_content', side_effect=Exception("API Rate limit exceeded")):
                # Gemini API例外が発生することを確認
                with pytest.raises(GeminiAPIError) as exc_info:
                    await bot.generate_idea(test_notes)
                
                # エラーメッセージにAPI関連情報が含まれることを確認
                assert "rate limit" in str(exc_info.value).lower() or \
                       "api" in str(exc_info.value).lower() or \
                       "gemini" in str(exc_info.value).lower()