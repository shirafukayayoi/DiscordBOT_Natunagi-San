import discord
from discord.ext import commands
import os
import json
from command.GoogleCalendarTemplate import CalendarMain
from function.rss_handler import RSSHandler

# configファイルのパス
CONFIG_FILE = "config.json"

# configを保存・読み込みする関数
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rss_urls": []}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# ボットのクラス
class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents, config):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.config = config
        self.rss_urls = config.get("rss_urls", [])
        self.channel_id = 1267847147676762194  # チャンネルIDをここで設定（または環境変数から取得）

    async def setup_hook(self):
        await self.tree.sync()
        print('Commands synced.')

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

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

# ボットを実行
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("TOKEN環境変数が設定されていません")

bot.run(TOKEN)
