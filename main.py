"""
Discord LLM Bot - メインモジュール

GitHub → Gemini → Discord のアイデア生成・投稿ボット
Fail-Fast原則に基づく例外管理とカスタムエラー処理
"""

import discord
from discord.ext import commands
from settings import DISCORD_BOT_TOKEN, GITHUB_TOKEN, OBSIDIAN_REPO_OWNER, OBSIDIAN_REPO_NAME, RANDOM_NOTES_COUNT, GEMINI_API_KEY, IDEA_MAX_LENGTH
import logging
from typing import Optional, List
from github import Github
import random
import google.genai as genai


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


class GeminiAPIError(Exception):
    """Gemini API例外"""
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
            
            # Gemini クライアント初期化
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                
                logger.info("🧠 Gemini client initialized successfully")
                
            except Exception as gemini_error:
                logger.error(f"Gemini client initialization failed: {gemini_error}")
                raise GeminiAPIError(f"Failed to initialize Gemini client: {gemini_error}") from gemini_error
            
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

    def _format_idea_prompt(self, notes: List[str]) -> str:
        """
        アイデア生成プロンプト整形
        
        Args:
            notes: Obsidianノート断片のリスト
            
        Returns:
            str: 整形されたGeminiプロンプト
        """
        # ノート断片を整形・結合
        notes_text = "\n\n---\n\n".join(notes[:5])  # 最大5件に制限
        
        prompt = f"""あなたは創作物語のアイデア生成の専門家です。以下のObsidianノート断片を参考に、魅力的な物語コンセプトを1つ生成してください。

【ノート断片】
{notes_text}

【生成ルール】
✅ 物語の核となる独創的なアイデア・コンセプトを提示
✅ 複数のノート要素を創造的に組み合わせて発展
✅ 読者の興味を引く具体的な設定・キャラクター・世界観を含む
✅ 簡潔で魅力的な日本語（{IDEA_MAX_LENGTH}文字以内）
✅ 「〜物語」「〜の話」などの決まり文句を避け、直接的な表現で

【出力フォーマット】
物語アイデア：[ここに生成されたアイデアを記述]

物語アイデア："""
        
        return prompt

    async def generate_idea(self, notes: List[str]) -> str:
        """
        Gemini API経由でアイデア生成
        
        Args:
            notes: Obsidianノート断片のリスト
            
        Returns:
            str: 生成された創作アイデア
            
        Raises:
            GeminiAPIError: Gemini API関連エラー
        """
        try:
            if not notes:
                logger.warning("⚠️  No notes provided for idea generation")
                return "ノートが見つかりませんでした。新しいノートを追加してからお試しください。"
            
            logger.info(f"🧠 Generating idea from {len(notes)} notes")
            
            # プロンプト整形
            prompt = self._format_idea_prompt(notes)
            logger.debug(f"Generated prompt: {len(prompt)} characters")
            
            # Gemini API呼び出し
            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config={
                    'temperature': 0.8,  # 創造性を高める
                    'max_output_tokens': 1000,
                    'top_p': 0.9,
                    'top_k': 40
                }
            )
            
            # レスポンステキスト抽出・整形
            if not hasattr(response, 'text') or not response.text:
                logger.warning("⚠️  Empty response from Gemini API")
                return "アイデア生成に失敗しました。しばらく待ってからお試しください。"
            
            idea = response.text.strip()
            
            # 品質チェック
            if len(idea) < 10:
                logger.warning(f"⚠️  Generated idea too short: {len(idea)} chars")
                return "短すぎるアイデアが生成されました。再試行してください。"
            
            # 長さ制限チェック
            if len(idea) > IDEA_MAX_LENGTH:
                logger.info(f"✂️  Truncating idea from {len(idea)} to {IDEA_MAX_LENGTH} chars")
                idea = idea[:IDEA_MAX_LENGTH - 3] + "..."
            
            logger.info(f"✨ Successfully generated idea: {len(idea)} characters")
            return idea
            
        except Exception as e:
            error_msg = f"Failed to generate idea with Gemini API: {e}"
            logger.error(f"❌ {error_msg}")
            
            # API制限エラーの詳細処理
            if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                error_msg = f"Gemini API rate limit exceeded: {e}"
            elif "authentication" in str(e).lower() or "api key" in str(e).lower():
                error_msg = f"Gemini API authentication failed: {e}"
            
            raise GeminiAPIError(error_msg) from e


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