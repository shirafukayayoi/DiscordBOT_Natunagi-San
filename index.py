import discord
from discord.ext import commands

import os
import json
from command.GoogleCalendarTemplate import CalendarMain
from function.rss_handler import RSSHandler
from discord.ext import tasks
import asyncio
from function.task_message import TaskMessage
from typing import List
from discord import app_commands

# configファイルのパス
CONFIG_FILE = "config.json"

# configを保存・読み込みする関数
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rss_urls": [], "minutes": 0}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# ボットのクラス
class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents, config):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.config = config
        self.rss_urls = config.get("rss_urls", [])
        self.channel_id = int(os.environ["CHANNEL_ID"])  # チャンネルIDをここで設定（または環境変数から取得）

    async def setup_hook(self):
        await self.tree.sync()
        print('Commands synced.')

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        global task_message_instance
        task_message_instance = TaskMessage(self)  # TaskMessageのインスタンスを作成
        task_message_instance.start()

        # コマンドの登録状態を確認する
        for command in self.tree.get_commands():
            print(f'Command: {command.name}')
        print('------')

        # ステータス設定
        activity = discord.Streaming(name="夏凪優羽がサポートするよ！！！", url="https://www.twitch.tv/shirafukayayoi")
        await self.change_presence(status=discord.Status.online, activity=activity)

        # チャンネルの取得とRSSフィードのチェックを開始
        channel = self.get_channel(self.channel_id)
        if channel is None:
            print(f"チャンネルID {self.channel_id} が見つかりません。")
            return

        self.rss_handler = RSSHandler(self)
        self.loop.create_task(self.rss_handler.check_rss_feed())

    def add_rss_url(self, url):
        if self.rss_handler.add_rss_url(url):
            self.config["rss_urls"] = self.rss_urls
            save_config(self.config)
            return True
        return False


# intentsの設定
intents = discord.Intents.default()
intents.message_content = True

# configの読み込み
config = load_config()

# ボットの初期化
bot = MyBot(command_prefix="!", intents=intents, config=config)

# グローバル変数を定義
task_message_instance = None

# スラッシュコマンドの定義
@bot.tree.command(name="hello", description="Says hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

@bot.tree.command(name='calendarpush', description='Googleカレンダーにイベントを追加します')
async def calendarpush(interaction: discord.Interaction, eventname: str, eventdate: str):
    if len(eventdate) != 8 or not eventdate.isdigit():
        await interaction.response.send_message("日付は20240801のように入力してください")
        return

    try:
        calendarpush = CalendarMain(eventname, eventdate)
        await interaction.response.send_message(f"イベント名: `{eventname}`\n日付: `{eventdate}`\nを追加しました")
    except Exception as e:
        await interaction.response.send_message(f"エラーが発生しました: {e}")

@bot.tree.command(name='set-rss', description='RSSフィードのURLを追加します')
async def setrss(interaction: discord.Interaction, url: str):
    if bot.add_rss_url(url):
        await interaction.response.send_message(f"RSS URLが追加されました: {url}")
    else:
        await interaction.response.send_message(f"このRSS URLは既に追加されています。")

@bot.tree.command(name='list-rss', description='登録されているRSSフィードのURLを表示します')
async def listrss(interaction: discord.Interaction):
    if bot.rss_urls:
        url_list = "\n".join(bot.rss_urls)
        await interaction.response.send_message(f"登録されているRSS URLリスト:\n{url_list}")
    else:
        await interaction.response.send_message("現在、登録されているRSS URLはありません。")

@bot.tree.command(name='remove-rss', description='登録されているRSSフィードのURLを削除します')
async def removerss(interaction: discord.Interaction, url: str):
    if url in bot.rss_urls:
        bot.rss_urls.remove(url)
        bot.config["rss_urls"] = bot.rss_urls
        save_config(bot.config)
        await interaction.response.send_message(f"RSS URLが削除されました: {url}")
    else:
        await interaction.response.send_message(f"このRSS URLは登録されていません。")

INTERVAL_MINUTES = 0
task_message_instance = None

@bot.tree.command(name='send-minute', description='指定した分数ごとにメッセージを送信するための時間を設定します')
async def send_minute(interaction: discord.Interaction, minutes: int):
    global INTERVAL_MINUTES
    global task_message_instance

    # 1. 分数の設定と保存
    INTERVAL_MINUTES = minutes
    bot.config["minutes"] = minutes
    save_config(bot.config)

    # 2. 既存のタスクインスタンスがあればキャンセル
    if task_message_instance:
        task_message_instance.cancel()

    # 3. 新しいタスクインスタンスを作成して開始
    task_message_instance = TaskMessage(bot)
    task_message_instance.start()

    await interaction.response.send_message(f"メッセージ送信間隔を{minutes}分に設定しました。以下のメッセージが送信されます。")


async def autocomplete_playlist(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    fruits = ["とにかく詰め込め！", "ブルーアーカイブOST"]
    choices = []
    playlist = interaction.data.get("options")[0].get("value")
    for fruit in fruits:
        if playlist.lower() in fruit.lower():
            choices.append(app_commands.Choice(name=fruit, value=fruit))
    return choices

@bot.tree.command(name='summon-playlist', description='プレイリストを呼び出します')
@app_commands.autocomplete(playlist=autocomplete_playlist)
async def summon_playlist(interaction: discord.Interaction, playlist: str):
    if playlist == "とにかく詰め込め！":
        await interaction.response.send_message("https://youtube.com/playlist?list=PLHh1qLt2rZLK4QFgf_W0pZLAMSiipfT3o&si=pf23FQmirl2agzLt")
    elif playlist == "ブルーアーカイブOST":
        await interaction.response.send_message("https://youtube.com/playlist?list=PLh6Ws4Fpphfqr7VL72Q6HK5Ole9YI54hv&si=yL9IWx3zvuuw3YcP")
        # ここに特定のURLをメッセージ送信するコードを追加してください

# ボットを実行
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("TOKEN環境変数が設定されていません")

bot.run(TOKEN)
