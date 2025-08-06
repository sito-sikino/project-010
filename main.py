"""
Discord LLM Bot - メインモジュール

GitHub → Gemini → Discord のアイデア生成・投稿ボット
Fail-Fast原則に基づく例外管理とカスタムエラー処理
"""

import discord
from discord.ext import commands
from settings import DISCORD_BOT_TOKEN
import logging
from typing import Optional


# 構造化ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscordAPIError(Exception):
    """Discord API例外"""
    pass


class DiscordIdeaBot(commands.Bot):
    """
    Discord アイデア生成ボット
    
    GitHub API → Gemini API → Discord API の統合フロー実行
    Fail-Fast原則により、エラー発生時は即座に停止
    """
    
    def __init__(self) -> None:
        """Bot初期化"""
        try:
            # Discord Intents設定（基本権限）
            intents = discord.Intents.default()
            
            # Bot初期化 (commands.Bot継承)
            super().__init__(
                command_prefix='!',
                intents=intents,
                case_insensitive=True
            )
            
            logger.info("DiscordIdeaBot successfully initialized")
            
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")
            raise DiscordAPIError(f"Failed to initialize Discord bot: {e}") from e
    
    async def on_ready(self) -> None:
        """Bot起動完了イベント"""
        try:
            if self.user:
                logger.info(f'🤖 {self.user} successfully logged in to Discord!')
                logger.info(f'📝 Bot ID: {self.user.id}')
                logger.info(f'🔗 Connected to {len(self.guilds)} servers')
            else:
                logger.warning('⚠️  Bot ready event triggered (user info not available)')
                
        except Exception as e:
            logger.error(f"Error in on_ready event: {e}")
            raise DiscordAPIError(f"Failed in ready event: {e}") from e
    
    async def on_error(self, event: str, *args, **kwargs) -> None:
        """グローバルエラーハンドラー"""
        logger.error(f"Unexpected error in event '{event}': {args}")
        # Fail-Fast: 重大なエラー時は即座に停止
        await self.close()


def main() -> None:
    """
    メイン実行関数
    
    Fail-Fast原則により、初期化エラーは即座にプログラムを停止
    """
    try:
        logger.info("🚀 Starting Discord LLM Bot...")
        
        # Bot インスタンス作成
        bot = DiscordIdeaBot()
        
        # Discord Bot実行
        logger.info("🔌 Connecting to Discord...")
        bot.run(DISCORD_BOT_TOKEN)
        
    except DiscordAPIError as e:
        logger.error(f"❌ Discord API Error: {e}")
        raise
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise DiscordAPIError(f"Bot execution failed: {e}") from e


if __name__ == '__main__':
    main()