"""
Discord LLM Bot - メインモジュール

GitHub → Gemini → Discord のアイデア生成・投稿ボット
Fail-Fast原則に基づく例外管理とカスタムエラー処理
"""

import discord
from discord.ext import commands, tasks
from settings import DISCORD_BOT_TOKEN, GITHUB_TOKEN, OBSIDIAN_REPO_OWNER, OBSIDIAN_REPO_NAME, RANDOM_NOTES_COUNT, GEMINI_API_KEY, IDEA_MAX_LENGTH, DISCORD_CHANNEL_ID, POSTING_INTERVAL
import logging
from typing import Optional, List
from github import Github
import random
import google.genai as genai
import time


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
            
            # スケジューラータスク開始 (Bot ready後)
            if not self.generate_and_post_idea.is_running():
                self.generate_and_post_idea.start()
                logger.info("🔄 Scheduled task started after bot ready")
                
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

    def _format_discord_message(self, idea: str) -> str:
        """
        Discord投稿用メッセージフォーマット
        
        Discord 2000文字制限に対応し、装飾付きテンプレートで投稿メッセージを整形
        
        Args:
            idea: 生成されたアイデア (Gemini API出力)
            
        Returns:
            str: フォーマット済みDiscordメッセージ (2000文字以内保証)
        """
        # メッセージテンプレート定数
        TEMPLATE_HEADER = "✨ **新しい創作アイデア**\n\n"
        TEMPLATE_FOOTER = "\n\n---\n🤖 *Discord LLM Bot による自動生成*"
        DISCORD_MAX_LENGTH = 2000
        TRUNCATION_SUFFIX = "..."
        
        # 基本メッセージ構築
        formatted_message = f"{TEMPLATE_HEADER}{idea}{TEMPLATE_FOOTER}"
        
        # Discord文字数制限チェック・対応
        if len(formatted_message) <= DISCORD_MAX_LENGTH:
            return formatted_message
            
        # 長文の場合: アイデア部分を動的調整
        template_overhead = len(TEMPLATE_HEADER) + len(TEMPLATE_FOOTER) + len(TRUNCATION_SUFFIX)
        max_idea_length = DISCORD_MAX_LENGTH - template_overhead
        
        if max_idea_length > 0:
            truncated_idea = idea[:max_idea_length] + TRUNCATION_SUFFIX
            return f"{TEMPLATE_HEADER}{truncated_idea}{TEMPLATE_FOOTER}"
        else:
            # 極端ケース: 最小限メッセージ
            logger.warning("⚠️  Idea too long, using minimal message format")
            return f"✨ アイデア生成完了\n\n{idea[:1950]}{TRUNCATION_SUFFIX}"

    async def post_to_discord(self, idea: str) -> None:
        """
        Discord指定チャンネルにアイデア投稿
        
        Fail-Fast原則に従い、Discord API関連エラーは即座に停止
        
        Args:
            idea: 投稿するアイデア (空文字・None不可)
            
        Raises:
            DiscordAPIError: Discord API関連エラー (チャンネル取得失敗、投稿失敗等)
        """
        try:
            # 入力検証
            if not idea or not idea.strip():
                raise DiscordAPIError("Empty or whitespace-only idea cannot be posted")
            
            if not DISCORD_CHANNEL_ID:
                raise DiscordAPIError("DISCORD_CHANNEL_ID environment variable not configured")
            
            logger.info(f"💬 Starting Discord post to channel: {DISCORD_CHANNEL_ID}")
            logger.debug(f"Idea preview: {idea[:50]}{'...' if len(idea) > 50 else ''}")
            
            # チャンネル取得・検証
            try:
                channel_id = int(DISCORD_CHANNEL_ID)
            except ValueError as ve:
                raise DiscordAPIError(f"Invalid DISCORD_CHANNEL_ID format: {DISCORD_CHANNEL_ID}") from ve
                
            channel = self.get_channel(channel_id)
            if not channel:
                raise DiscordAPIError(
                    f"Failed to access Discord channel {channel_id}. "
                    f"Verify bot permissions and channel existence."
                )
            
            # メッセージフォーマット・検証
            formatted_message = self._format_discord_message(idea)
            
            if len(formatted_message) > 2000:
                logger.error(f"❌ Formatted message exceeds Discord limit: {len(formatted_message)} chars")
                raise DiscordAPIError("Message formatting failed: exceeds 2000 character limit")
            
            # Discord API投稿実行
            message_obj = await channel.send(formatted_message)
            
            logger.info(f"✅ Successfully posted to Discord")
            logger.info(f"📊 Message stats: {len(formatted_message)} chars, ID: {message_obj.id}")
            
        except DiscordAPIError:
            # DiscordAPIError は再発生 (Fail-Fast)
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error during Discord posting: {e}"
            logger.error(f"❌ {error_msg}")
            
            # 詳細エラー分類
            if "HTTPException" in str(type(e)):
                error_msg = f"Discord API HTTP error: {e}"
            elif "Forbidden" in str(e):
                error_msg = f"Discord bot lacks permissions: {e}"
            elif "NotFound" in str(e):
                error_msg = f"Discord channel not found: {e}"
            
            raise DiscordAPIError(error_msg) from e

    @tasks.loop(minutes=POSTING_INTERVAL)
    async def generate_and_post_idea(self) -> None:
        """
        統合フロー: GitHub→Gemini→Discord
        
        10分間隔での自動アイデア生成・投稿実行
        Fail-Fast原則により、各段階でのエラーは即座に停止
        処理時間計測・詳細ログ出力・段階的エラー分類
        
        Raises:
            GitHubAPIError: GitHub API関連エラー
            GeminiAPIError: Gemini API関連エラー  
            DiscordAPIError: Discord API関連エラー
        """
        flow_start_time = time.time()
        current_loop = self.generate_and_post_idea.current_loop + 1
        
        try:
            logger.info(f"🔄 Starting scheduled flow #{current_loop} (interval: {POSTING_INTERVAL}min)")
            
            # 段階1: GitHub API - ランダムノート取得
            step1_start = time.time()
            logger.info("📁 Phase 1/3: Fetching random notes from GitHub...")
            notes = await self.get_random_notes()
            step1_time = time.time() - step1_start
            logger.info(f"✅ Phase 1 completed: {len(notes)} notes loaded ({step1_time:.2f}s)")
            
            # 段階2: Gemini API - アイデア生成
            step2_start = time.time()
            logger.info("🧠 Phase 2/3: Generating creative idea with Gemini...")
            idea = await self.generate_idea(notes)
            step2_time = time.time() - step2_start
            logger.info(f"✅ Phase 2 completed: {len(idea)} chars idea generated ({step2_time:.2f}s)")
            
            # 段階3: Discord API - 投稿
            step3_start = time.time()
            logger.info("💬 Phase 3/3: Posting idea to Discord...")
            await self.post_to_discord(idea)
            step3_time = time.time() - step3_start
            logger.info(f"✅ Phase 3 completed: idea posted to Discord ({step3_time:.2f}s)")
            
            # 統合フロー完了統計
            total_time = time.time() - flow_start_time
            logger.info(f"🎉 Scheduled flow #{current_loop} completed successfully")
            logger.info(f"📊 Performance: Total {total_time:.2f}s (GitHub:{step1_time:.1f}s, Gemini:{step2_time:.1f}s, Discord:{step3_time:.1f}s)")
            
        except GitHubAPIError as e:
            total_time = time.time() - flow_start_time
            logger.error(f"❌ Flow #{current_loop} failed at Phase 1 (GitHub): {e} ({total_time:.2f}s)")
            raise  # Fail-Fast: GitHub API失敗時は即座停止
            
        except GeminiAPIError as e:
            total_time = time.time() - flow_start_time
            logger.error(f"❌ Flow #{current_loop} failed at Phase 2 (Gemini): {e} ({total_time:.2f}s)")
            raise  # Fail-Fast: Gemini API失敗時は即座停止
            
        except DiscordAPIError as e:
            total_time = time.time() - flow_start_time
            logger.error(f"❌ Flow #{current_loop} failed at Phase 3 (Discord): {e} ({total_time:.2f}s)")
            raise  # Fail-Fast: Discord API失敗時は即座停止
            
        except Exception as e:
            total_time = time.time() - flow_start_time
            logger.error(f"❌ Flow #{current_loop} failed with unexpected error: {e} ({total_time:.2f}s)")
            # 予期しないエラーもFail-Fastで処理
            raise DiscordAPIError(f"Unexpected error in scheduled flow: {e}") from e

    @generate_and_post_idea.before_loop
    async def before_generate_and_post_idea(self) -> None:
        """
        スケジュールタスク開始前処理
        
        Discord Bot Ready状態まで待機し、初期化完了確認
        API疎通確認・設定値ログ出力
        """
        logger.info("⏳ Scheduler initialization: waiting for bot ready state...")
        await self.wait_until_ready()
        
        logger.info("🚀 Bot ready state confirmed, starting scheduled task setup")
        logger.info(f"⚙️  Scheduler configuration:")
        logger.info(f"   - Interval: {POSTING_INTERVAL} minutes")
        logger.info(f"   - Random notes count: {RANDOM_NOTES_COUNT}")
        logger.info(f"   - Idea max length: {IDEA_MAX_LENGTH} chars")
        logger.info(f"   - Target Discord channel: {DISCORD_CHANNEL_ID}")
        
        # 初回実行通知
        logger.info("🎯 First scheduled execution will begin shortly...")
        logger.info(f"📅 Subsequent executions every {POSTING_INTERVAL} minutes")


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