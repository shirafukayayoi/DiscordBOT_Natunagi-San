import discord
from discord.ext import commands
import os
import json
from function.rss_handler import RSSHandler
from function.youtube_notification import YoutubeNotification
from function.task_message import TaskMessage

# configファイルのパス
CONFIG_FILE = "config.json"

# configを保存・読み込みする関数
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rss_urls": [], "youtube_rss": [], "minutes": 0}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# ボットのクラス
# MyBotクラスの定義
class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents, config):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.config = config
        self.rss_urls = config.get("rss_urls", [])
        self.youtube_rss = config.get("youtube_rss", [])
        self.task_message_instance = None  # TaskMessageインスタンスを保持するプロパティを追加

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        
        # TaskMessageのインスタンスを作成
        self.task_message_instance = TaskMessage(self)  
        print('TaskMessage instance created.')
        self.task_message_instance.start()

        # コマンドの同期
        await self.tree.sync()
        print('Commands synchronized.')
        
        # コマンドの登録状態を確認する
        for command in self.tree.get_commands():
            print(f'Command: {command.name}')
        print('-------------------------')

        # ステータス設定
        activity = discord.Streaming(name="夏凪優羽がサポートするよ！！！", url="https://www.twitch.tv/shirafukayayoi")
        await self.change_presence(status=discord.Status.online, activity=activity)

        self.rss_handler = RSSHandler(self)
        self.loop.create_task(self.rss_handler.check_rss_feed())

        self.youtube_notification = YoutubeNotification(self)
        self.loop.create_task(self.youtube_notification.check_rss_feed())

    def add_rss_url(self, url):
        if url not in self.rss_urls:
            self.rss_urls.append(url)
            self.config["rss_urls"] = self.rss_urls
            save_config(self.config)
            return True
        return False

    def add_youtube_rss_url(self, name, url):
        # 既に追加されているかチェック
        for entry in self.youtube_rss:
            if isinstance(entry, dict) and entry.get("url") == url:
                return False  # すでに追加されている場合

        # 新しいYouTube RSS URLを追加
        self.youtube_rss.append({"name": name, "url": url})
        self.config["youtube_rss"] = self.youtube_rss
        save_config(self.config)
        return True

# intentsの設定
intents = discord.Intents.default()
intents.message_content = True

# configの読み込み
config = load_config()

# ボットの初期化
bot = MyBot(command_prefix="!", intents=intents, config=config)

# グローバル変数を定義
task_message_instance = None

# コマンドのセットアップ
import commands
commands.setup(bot)

# ボットの起動
bot.run(os.environ["TOKEN"])