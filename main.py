"""
Discord LLM Bot - メインモジュール

GitHub → Gemini → Discord のアイデア生成・投稿ボット
Fail-Fast原則に基づく例外管理とカスタムエラー処理
"""

import discord
from discord.ext import commands, tasks
from settings import DISCORD_BOT_TOKEN, GITHUB_TOKEN, OBSIDIAN_REPO_OWNER, OBSIDIAN_REPO_NAME, RANDOM_NOTES_COUNT, GEMINI_API_KEY, IDEA_MAX_LENGTH, DISCORD_CHANNEL_ID, POSTING_INTERVAL_MINUTES, TARGET_FOLDER
import logging
from typing import Optional, List
from github import Github
import random
import google.genai as genai
import time


# 構造化ログ設定（ファイル出力追加）
import logging.handlers

# ログディレクトリ作成
import os
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# ファイルハンドラーとコンソールハンドラーの設定
file_handler = logging.FileHandler(f'{log_dir}/discord_bot.log', encoding='utf-8')
console_handler = logging.StreamHandler()

# フォーマッター設定
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# ルートロガー設定
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
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

    def _get_folder_markdown_files(self, repo, folder_path: str) -> List:
        """
        指定フォルダからMarkdownファイルを取得
        
        Args:
            repo: GitHub リポジトリオブジェクト
            folder_path: 対象フォルダパス (例: "20_Literature")
            
        Returns:
            List: Markdownファイルのリスト
        """
        markdown_files = []
        try:
            logger.info(f"📂 Searching in folder: {folder_path}")
            contents = repo.get_contents(folder_path)
            
            if isinstance(contents, list):
                for content in contents:
                    if content.type == 'file' and content.name.endswith(('.md', '.markdown')):
                        markdown_files.append(content)
                        logger.debug(f"   📝 Found: {content.name}")
            else:
                # 単一ファイルの場合
                if contents.name.endswith(('.md', '.markdown')):
                    markdown_files.append(contents)
                    
        except Exception as e:
            logger.warning(f"⚠️  Could not access folder '{folder_path}': {e}")
            
        return markdown_files

    def _filter_markdown_files(self, files) -> List:
        """Markdownファイルをフィルタリング（互換性保持）"""
        markdown_files = []
        for file in files:
            if file.type == 'file' and file.name.endswith(('.md', '.markdown')):
                markdown_files.append(file)
        return markdown_files

    async def get_random_notes(self) -> tuple[List[str], List[str]]:
        """
        GitHub API経由でランダムObsidianノート取得
        
        Returns:
            tuple[List[str], List[str]]: (取得したMarkdownノートの内容リスト, ファイル名リスト)
            
        Raises:
            GitHubAPIError: GitHub API関連エラー
        """
        try:
            logger.info(f"📁 Fetching random notes from {self.repo_owner}/{self.repo_name}")
            
            # リポジトリ取得
            repo = self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
            
            # 指定フォルダからMarkdownファイル取得
            if TARGET_FOLDER:
                markdown_files = self._get_folder_markdown_files(repo, TARGET_FOLDER)
                logger.info(f"📝 Found {len(markdown_files)} markdown files in '{TARGET_FOLDER}' folder")
            else:
                # フォルダ指定なしの場合はルートのみ検索（従来動作）
                all_files = repo.get_contents("")
                markdown_files = self._filter_markdown_files(all_files)
                logger.info(f"📝 Found {len(markdown_files)} markdown files in root")
            
            if len(markdown_files) == 0:
                target_info = f" in '{TARGET_FOLDER}' folder" if TARGET_FOLDER else " in repository"
                logger.warning(f"⚠️  No markdown files found{target_info}")
                return [], []
            
            # 取得数を調整
            count = min(RANDOM_NOTES_COUNT, len(markdown_files))
            selected_files = random.sample(markdown_files, count)
            logger.info(f"🎲 Selected {count} random files")
            
            # 選択されたファイル名をログに記録
            for i, file in enumerate(selected_files):
                logger.info(f"📄 File {i+1}: {file.name} ({file.size} bytes)")
            
            # ファイル内容取得（サイズ制限付き）
            notes = []
            note_titles = []
            for file in selected_files:
                try:
                    # ファイルサイズチェック（1MB制限）
                    if file.size > 1024 * 1024:
                        logger.warning(f"⚠️  Skipping large file: {file.name} ({file.size} bytes)")
                        continue
                    
                    content = file.decoded_content.decode('utf-8')
                    notes.append(content)
                    note_titles.append(file.name)
                    logger.info(f"✅ Loaded: {file.name} ({len(content)} chars)")
                    
                except UnicodeDecodeError:
                    logger.warning(f"⚠️  Skipping binary file: {file.name}")
                    continue
                    
                except Exception as file_error:
                    logger.warning(f"⚠️  Failed to load file {file.name}: {file_error}")
                    continue
            
            logger.info(f"🎯 Successfully loaded {len(notes)} notes")
            return notes, note_titles
            
        except Exception as e:
            error_msg = f"Failed to get random notes from GitHub: {e}"
            logger.error(f"❌ {error_msg}")
            raise GitHubAPIError(error_msg) from e

    def _format_idea_prompt(self, notes: List[str]) -> str:
        """
        完全オリジナル創作要素生成プロンプト整形（思考プロセス可視化対応）
        
        既存作品分析から抽象化→醸成→完全オリジナル構築のプロセスを実行
        思考過程を段階的に明示し、ログで詳細な推論プロセスを確認可能
        既存の固有名詞を一切使用せず、ログライン・世界観・主要キャラクター(最大3名)を生成
        
        Args:
            notes: Obsidianノート断片のリスト（既存作品分析情報）
            
        Returns:
            str: 思考プロセス明示+抽象化→醸成→完全オリジナル創造プロセス指定のGeminiプロンプト
        """
        # ノート断片を整形・結合（全量処理でGemini 2.0の大容量活用）
        notes_text = "\n\n---\n\n".join(notes[:3])  # 最大3件の既存作品分析データ
        
        prompt = f"""以下のObsidianノート情報を参考に、完全オリジナルな物語の基礎コンセプト案を1つ生成してください。

【ノート情報】
{notes_text}

【思考プロセス要求】
以下の段階を明確に分けて、詳細な推論過程を示してください：

**STEP1: ノート分析**
各ノートから抽出した主要な「テーマ・世界観・ストーリー・モチーフ・象徴体系・備考」要素を列挙

**STEP2: 抽象化プロセス**  
抽出要素を概念レベルまで抽象化（固有名詞・具体的設定を除去し、本質的テーマ・構造・関係性のみ抽出）

**STEP3: 組み合わせ推論**
抽象化された要素同士をどのように組み合わせ、新しい概念体系を構築するかの判断理由

**STEP4: コンセプト開発**
組み合わせから生まれる独創的な世界観・キャラクター・ストーリー核心の創造過程

---

【生成ルール】
✅ 既存作品の固有名詞・キャラクター・概念・組織名は絶対に使用しない
✅ 抽象化された概念から独創的な新要素を創造
✅ 完全オリジナルのログライン・世界観・キャラクターを構築
✅ 簡潔で魅力的な日本語（最終出力は{IDEA_MAX_LENGTH}文字以内）

【重要：出力形式の厳守】
必ず以下の手順で出力してください：

1. まず思考プロセス（STEP1-4）を詳細に記載
2. その後、必ず「**FINAL_OUTPUT**」という区切りを記載  
3. 最後に最終出力のみを記載

【最終出力フォーマット（必須）】
**FINAL_OUTPUT**
**ログライン**：[1行で物語の核心を表現]

**世界観**：[独創的な舞台設定・時代背景]

**主要キャラクター**：
1. [主人公の名前・設定・動機]
2. [重要キャラ2の名前・役割・特徴]  
3. [重要キャラ3の名前・役割・対立軸]

重要：思考プロセスと最終出力を「**FINAL_OUTPUT**」で明確に区切ってください。"""
        
        return prompt

    def _extract_thinking_process(self, response_text: str) -> tuple[str, str]:
        """
        Geminiレスポンスから思考プロセスと最終出力を分離（堅牢性強化版）
        
        STEP1-4の思考プロセスとFINAL_OUTPUTセクションを分離し、
        Geminiの不安定な出力フォーマットに対しても確実に分離処理を実行
        
        Args:
            response_text: Gemini APIからの生レスポンステキスト
            
        Returns:
            tuple[str, str]: (思考プロセス部分, 最終出力部分)
        """
        try:
            # Phase 1: 優先度順の分割パターンで検出
            split_patterns = [
                "**FINAL_OUTPUT**",
                "【最終出力】", 
                "## 最終出力",
                "**ログライン**：",
                "**ログライン**:",
                "■ログライン:",
                "ログライン：",
                "ログライン:",
            ]
            
            thinking_process = ""
            final_output = ""
            
            for pattern in split_patterns:
                if pattern in response_text:
                    if "ログライン" in pattern:
                        # ログライン以降を最終出力として扱う
                        logline_index = response_text.find(pattern)
                        thinking_process = response_text[:logline_index].strip()
                        final_output = response_text[logline_index:].strip()
                    else:
                        # 通常の分割処理
                        parts = response_text.split(pattern, 1)
                        thinking_process = parts[0].strip()
                        final_output = parts[1].strip() if len(parts) > 1 else ""
                    
                    logger.info(f"✅ Found separator pattern: {pattern}")
                    break
            
            # Phase 2: パターンが見つからない場合の高度なコンテンツ分析
            if not final_output:
                logger.warning("⚠️  No separator pattern found, analyzing content structure...")
                
                # 最終出力マーカーの検索（拡張版）
                final_markers = [
                    "**ログライン**", "**世界観**", "**主要キャラクター**",
                    "■ログライン", "■世界観", "■主要キャラクター",
                    "ログライン", "世界観", "主要キャラクター",
                    "物語コンセプト", "設定", "キャラクター"
                ]
                
                marker_positions = []
                for marker in final_markers:
                    pos = response_text.find(marker)
                    if pos >= 0:
                        marker_positions.append(pos)
                
                if marker_positions:
                    # 最初の最終出力マーカー以降を最終出力とする
                    split_pos = min(marker_positions)
                    thinking_process = response_text[:split_pos].strip()
                    final_output = response_text[split_pos:].strip()
                    logger.info(f"✅ Content structure analysis successful, split at position {split_pos}")
                else:
                    logger.warning("⚠️  No content structure markers found, using emergency fallback...")
                    
                    # Phase 3: 緊急時フォールバック - STEPパターン終了位置を検出
                    step_end_patterns = ["STEP4:", "**STEP4:", "4."]
                    step_end_pos = -1
                    
                    for step_pattern in step_end_patterns:
                        pos = response_text.find(step_pattern)
                        if pos >= 0:
                            # STEP4の終了位置を探す（次の段落まで）
                            step_content_start = pos + len(step_pattern)
                            next_double_newline = response_text.find("\n\n", step_content_start)
                            if next_double_newline > 0:
                                step_end_pos = next_double_newline
                                break
                    
                    if step_end_pos > 0:
                        thinking_process = response_text[:step_end_pos].strip()
                        final_output = response_text[step_end_pos:].strip()
                        logger.info(f"🆘 Emergency fallback successful, split after STEP4 at position {step_end_pos}")
                    else:
                        # 最終的フォールバック: 全体を最終出力として扱う（ただし思考プロセス警告）
                        logger.error("❌ All extraction methods failed, treating entire response as final output")
                        thinking_process = ""
                        final_output = response_text.strip()
            
            # Phase 4: 最終出力品質検証と安全チェック
            if final_output:
                # 思考プロセスが混入していないかの緊急チェック
                thinking_contamination = any(marker in final_output for marker in [
                    "**STEP1:", "**STEP2:", "**STEP3:", "**STEP4:",
                    "ノート分析", "抽象化プロセス", "組み合わせ推論", "コンセプト開発"
                ])
                
                if thinking_contamination:
                    logger.error("🚨 CRITICAL: Thinking process detected in final output!")
                    logger.error("🔧 Attempting emergency cleanup...")
                    
                    # 緊急クリーンアップ: 最終出力形式の箇所のみを抽出
                    cleanup_markers = ["**ログライン**", "■ログライン", "ログライン"]
                    for marker in cleanup_markers:
                        if marker in final_output:
                            marker_pos = final_output.find(marker)
                            cleaned_output = final_output[marker_pos:].strip()
                            # 思考プロセス要素が残っていないかチェック
                            if not any(contam in cleaned_output for contam in ["STEP", "ノート分析", "抽象化"]):
                                final_output = cleaned_output
                                logger.info("✅ Emergency cleanup successful")
                                break
                    else:
                        # クリーンアップ失敗時のエラーメッセージ返却
                        logger.error("💥 Emergency cleanup failed - returning error message")
                        thinking_process = response_text[:500] + "..."  # デバッグ用に一部保存
                        final_output = "アイデア生成でフォーマットエラーが発生しました。しばらく待ってからお試しください。"
                
                # 出力形式完全性チェック
                has_logline = any(marker in final_output for marker in ["ログライン", "物語", "コンセプト"])
                has_worldview = any(marker in final_output for marker in ["世界観", "設定", "舞台"])
                has_characters = any(marker in final_output for marker in ["キャラクター", "登場人物", "主人公"])
                format_score = sum([has_logline, has_worldview, has_characters])
                
                logger.info(f"📝 Final output format completeness: {format_score}/3 sections")
                logger.info(f"🔍 Final output length: {len(final_output)} chars")
                
                if format_score == 0:
                    logger.warning("⚠️  Final output may be incomplete or malformed")
            
            # 思考プロセス品質チェック
            if thinking_process:
                step_count = sum(1 for step in ["STEP1:", "STEP2:", "STEP3:", "STEP4:"] 
                               if step in thinking_process)
                logger.info(f"🧠 Extracted thinking process with {step_count}/4 steps")
            
            return thinking_process, final_output
            
        except Exception as e:
            logger.error(f"❌ Failed to extract thinking process: {e}")
            # 緊急フォールバック: エラーメッセージを最終出力として返す
            return "", "アイデア生成処理でエラーが発生しました。しばらく待ってからお試しください。"

    async def generate_idea(self, notes: List[str], note_titles: List[str]) -> str:
        """
        Gemini API経由でアイデア生成（思考プロセス可視化対応・ログ最適化版）
        
        Geminiから思考プロセスと最終出力を分離し、
        重要な推論過程をクリーンなログで記録して、最終出力のみを返却
        
        Args:
            notes: Obsidianノート断片のリスト
            note_titles: ノートファイル名のリスト
            
        Returns:
            str: 最終出力部分のみ（Discord投稿用）
            
        Raises:
            GeminiAPIError: Gemini API関連エラー
        """
        try:
            if not notes:
                logger.warning("⚠️  No notes provided for idea generation")
                return "ノートが見つかりませんでした。新しいノートを追加してからお試しください。"
            
            logger.info(f"🧠 Generating idea from {len(notes)} notes")
            
            # 使用ノート概要をログに記録（簡潔版）
            note_info = [f"{title}({len(note)}chars)" for note, title in zip(notes, note_titles)]
            logger.info(f"📝 Input notes: {' | '.join(note_info)}")
            
            # プロンプト整形
            prompt = self._format_idea_prompt(notes)
            logger.info(f"📋 Prompt generated: {len(prompt)} chars")
            
            # Gemini API呼び出し
            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config={
                    'temperature': 0.8,  # 創造性を高める
                    'max_output_tokens': 2000,  # 思考プロセス分を増量
                    'top_p': 0.9,
                    'top_k': 40
                }
            )
            
            # レスポンステキスト抽出・整形
            if not hasattr(response, 'text') or not response.text:
                logger.warning("⚠️  Empty response from Gemini API")
                return "アイデア生成に失敗しました。しばらく待ってからお試しください。"
            
            full_response = response.text.strip()
            logger.info(f"📜 Received response: {len(full_response)} chars")
            
            # 思考プロセスと最終出力を分離
            thinking_process, final_output = self._extract_thinking_process(full_response)
            
            # 分離結果概要ログ
            logger.info(f"🔄 Processing: thinking({len(thinking_process)}) → final({len(final_output)}) chars")
            
            # 思考プロセスの詳細ログ記録（可視化対応）
            if thinking_process:
                logger.info("=" * 70)
                logger.info("🧠 GEMINI思考プロセス詳細:")
                logger.info("=" * 70)
                
                # STEPごとに詳細内容をログ記録
                steps = thinking_process.split("**STEP")
                for i, step in enumerate(steps):
                    if step.strip():
                        step_content = ("**STEP" + step) if i > 0 else step
                        # 各STEPの詳細を制限付きで表示（冗長さを避けつつ可視化）
                        display_content = step_content.strip()
                        
                        if len(display_content) > 1500:
                            # 長い場合は最初の1000文字 + 最後の200文字を表示
                            truncated = display_content[:1000] + "\n...[中略]...\n" + display_content[-200:]
                            logger.info(f"🔍 思考段階 {i if i == 0 else i}: {truncated}")
                        else:
                            logger.info(f"🔍 思考段階 {i if i == 0 else i}: {display_content}")
                        
                        # 各STEPの分析統計
                        if i > 0:  # STEP1-4のみ
                            note_analysis_count = display_content.count("**ノート") + display_content.count("ノート1") + display_content.count("ノート2") + display_content.count("ノート3")
                            if note_analysis_count > 0:
                                logger.info(f"   📊 分析要素数: {note_analysis_count}件")
                
                logger.info("=" * 70)
                logger.info("🎯 思考プロセス記録完了")
                logger.info("=" * 70)
            else:
                logger.warning("⚠️  No thinking process extracted")
            
            # 最終出力品質チェック
            if not final_output or len(final_output) < 10:
                logger.warning(f"⚠️  Final output too short: {len(final_output)} chars")
                return "短すぎるアイデアが生成されました。再試行してください。"
            
            # 長さ制限チェック（最終出力のみ）
            if len(final_output) > IDEA_MAX_LENGTH:
                logger.info(f"✂️  Truncating from {len(final_output)} to {IDEA_MAX_LENGTH} chars")
                final_output = final_output[:IDEA_MAX_LENGTH - 3] + "..."
            
            # 最終出力プレビュー（簡潔版）
            preview = final_output.replace('\n', ' ')[:100]
            logger.info(f"✨ Generated: {preview}{'...' if len(final_output) > 100 else ''}")
            
            return final_output
            
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

    @tasks.loop(minutes=POSTING_INTERVAL_MINUTES)
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
            logger.info(f"🔄 Starting scheduled flow #{current_loop} (interval: {POSTING_INTERVAL_MINUTES}min)")
            
            # 段階1: GitHub API - ランダムノート取得
            step1_start = time.time()
            logger.info("📁 Phase 1/3: Fetching random notes from GitHub...")
            notes, note_titles = await self.get_random_notes()
            step1_time = time.time() - step1_start
            logger.info(f"✅ Phase 1 completed: {len(notes)} notes loaded ({step1_time:.2f}s)")
            
            # 段階2: Gemini API - アイデア生成
            step2_start = time.time()
            logger.info("🧠 Phase 2/3: Generating creative idea with Gemini...")
            idea = await self.generate_idea(notes, note_titles)
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
        logger.info(f"   - Interval: {POSTING_INTERVAL_MINUTES} minutes")
        logger.info(f"   - Random notes count: {RANDOM_NOTES_COUNT}")
        logger.info(f"   - Idea max length: {IDEA_MAX_LENGTH} chars")
        logger.info(f"   - Target Discord channel: {DISCORD_CHANNEL_ID}")
        logger.info(f"   - Target folder: {TARGET_FOLDER if TARGET_FOLDER else 'Repository root'}")
        
        # 初回実行通知
        logger.info("🎯 First scheduled execution will begin shortly...")
        logger.info(f"📅 Subsequent executions every {POSTING_INTERVAL_MINUTES} minutes")


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