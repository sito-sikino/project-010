"""
Discord LLM Bot - メインモジュール

GitHub → Gemini → Discord のアイデア生成・投稿ボット
Fail-Fast原則に基づく例外管理とカスタムエラー処理
"""

import discord
from discord.ext import commands
from settings import DISCORD_BOT_TOKEN, GITHUB_TOKEN, OBSIDIAN_REPO_OWNER, OBSIDIAN_REPO_NAME, RANDOM_NOTES_COUNT
import logging
from typing import Optional, List
from github import Github
import random


# 構造化ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscordAPIError(Exception):
    """Discord API例外"""
    pass


class GitHubAPIError(Exception):
    """GitHub API例外"""
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
            
            # GitHub クライアント初期化
            try:
                from github import Auth
                auth = Auth.Token(GITHUB_TOKEN)
                self.github_client = Github(auth=auth)
                self.repo_owner = OBSIDIAN_REPO_OWNER
                self.repo_name = OBSIDIAN_REPO_NAME
                
                logger.info("🔑 GitHub client initialized successfully")
                
            except Exception as github_error:
                logger.error(f"GitHub client initialization failed: {github_error}")
                raise GitHubAPIError(f"Failed to initialize GitHub client: {github_error}") from github_error
            
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

    def _filter_markdown_files(self, files) -> List:
        """Markdownファイルをフィルタリング"""
        markdown_files = []
        for file in files:
            if file.type == 'file' and file.name.endswith(('.md', '.markdown')):
                markdown_files.append(file)
        return markdown_files

    async def get_random_notes(self) -> List[str]:
        """
        GitHub API経由でランダムObsidianノート取得
        
        Returns:
            List[str]: 取得したMarkdownノートの内容リスト
            
        Raises:
            GitHubAPIError: GitHub API関連エラー
        """
        try:
            logger.info(f"📁 Fetching random notes from {self.repo_owner}/{self.repo_name}")
            
            # リポジトリ取得
            repo = self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
            
            # 全ファイル一覧取得
            all_files = repo.get_contents("")
            logger.info(f"📄 Found {len(all_files)} total files")
            
            # Markdownファイルフィルタリング
            markdown_files = self._filter_markdown_files(all_files)
            logger.info(f"🔍 Filtered to {len(markdown_files)} markdown files")
            
            if len(markdown_files) == 0:
                logger.warning("⚠️  No markdown files found in repository")
                return []
            
            # 取得数を調整
            count = min(RANDOM_NOTES_COUNT, len(markdown_files))
            selected_files = random.sample(markdown_files, count)
            logger.info(f"🎲 Selected {count} random files")
            
            # ファイル内容取得（サイズ制限付き）
            notes = []
            for file in selected_files:
                try:
                    # ファイルサイズチェック（1MB制限）
                    if file.size > 1024 * 1024:
                        logger.warning(f"⚠️  Skipping large file: {file.name} ({file.size} bytes)")
                        continue
                    
                    content = file.decoded_content.decode('utf-8')
                    notes.append(content)
                    logger.debug(f"✅ Loaded: {file.name} ({len(content)} chars)")
                    
                except UnicodeDecodeError:
                    logger.warning(f"⚠️  Skipping binary file: {file.name}")
                    continue
                    
                except Exception as file_error:
                    logger.warning(f"⚠️  Failed to load file {file.name}: {file_error}")
                    continue
            
            logger.info(f"🎯 Successfully loaded {len(notes)} notes")
            return notes
            
        except Exception as e:
            error_msg = f"Failed to get random notes from GitHub: {e}"
            logger.error(f"❌ {error_msg}")
            raise GitHubAPIError(error_msg) from e


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