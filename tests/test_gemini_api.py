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
            test_titles = [
                "magical_forest.md",
                "time_travel.md", 
                "dragon_egg.md"
            ]
            
            # Gemini APIレスポンス（新しい形式）をモック化
            mock_response = MagicMock()
            mock_response.text = """■ログライン: 記憶を物質化できる青年が、消失した都市の真実を追う
■世界観: 2150年、記憶が実体化する技術により再構築された浮遊都市群
■主要キャラ: 記憶探偵リョウ(24)、消失事件の鍵を握る少女アヤ(16)、記憶商人の老人"""
            
            with patch.object(bot.gemini_client.models, 'generate_content', return_value=mock_response):
                # アイデア生成実行
                idea = await bot.generate_idea(test_notes, test_titles)
                
                # 結果検証（新しい構造化出力形式）
                assert isinstance(idea, str)
                assert len(idea) > 0
                # 新しい出力形式の基本要素を確認
                assert "■ログライン:" in idea
                assert "■世界観:" in idea
                assert "■主要キャラ:" in idea
                # 具体的なオリジナル要素を確認
                assert "記憶" in idea and "都市" in idea

    def test_prompt_formatting(self):
        """オリジナル創作要素プロンプト整形テスト"""
        # 新しい抽象化→醸成プロセスプロンプトのテスト
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_github_token',
            'GEMINI_API_KEY': 'test_gemini_key', 
            'DISCORD_BOT_TOKEN': 'test_discord_token',
            'OBSIDIAN_REPO_OWNER': 'test_owner',
            'OBSIDIAN_REPO_NAME': 'test_repo'
        }, clear=False):
            from main import DiscordIdeaBot
            
            bot = DiscordIdeaBot()
            
            # テスト用既存作品分析ノート
            test_notes = [
                "# エヴァンゲリオン分析\n人類補完計画、使徒との戦い、内面的な成長テーマ",
                "# 攻殻機動隊分析\nサイバーパンク世界観、義体と電脳、アイデンティティの探求", 
                "# AKIRA分析\n超能力による破壊と再生、権力構造への反抗、未来都市設定"
            ]
            
            # プロンプト整形メソッドが存在することを確認
            assert hasattr(bot, '_format_idea_prompt')
            
            # プロンプト整形実行
            formatted_prompt = bot._format_idea_prompt(test_notes)
            
            # プロンプトの基本構造確認
            assert isinstance(formatted_prompt, str)
            assert len(formatted_prompt) > 0
            
            # 既存作品分析データが含まれることを確認
            assert "エヴァンゲリオン分析" in formatted_prompt
            assert "攻殻機動隊分析" in formatted_prompt
            assert "AKIRA分析" in formatted_prompt
            
            # 抽象化→醸成プロセス指示が含まれることを確認
            assert "抽象化" in formatted_prompt
            assert "醸成" in formatted_prompt
            assert "オリジナル" in formatted_prompt
            
            # 新しい出力フォーマット指示が含まれることを確認
            assert "■ログライン:" in formatted_prompt
            assert "■世界観:" in formatted_prompt  
            assert "■主要キャラ:" in formatted_prompt
            
            # 重要指示が含まれることを確認
            assert "既存要素の直接利用・改変・オマージュは厳禁" in formatted_prompt
            assert "500文字以内" in formatted_prompt

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
            test_titles = ["test_note.md"]
            
            # API エラーをシミュレート
            with patch.object(bot.gemini_client.models, 'generate_content', side_effect=Exception("API Rate limit exceeded")):
                # Gemini API例外が発生することを確認
                with pytest.raises(GeminiAPIError) as exc_info:
                    await bot.generate_idea(test_notes, test_titles)
                
                # エラーメッセージにAPI関連情報が含まれることを確認
                assert "rate limit" in str(exc_info.value).lower() or \
                       "api" in str(exc_info.value).lower() or \
                       "gemini" in str(exc_info.value).lower()