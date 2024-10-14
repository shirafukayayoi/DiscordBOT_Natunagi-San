import json
import os

import discord
from discord.ext import commands

from function.rss_handler import RSSHandler
from function.task_message import TaskMessage
from function.youtube_notification import YoutubeNotification

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


import os
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import pytz
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class Youtube:
    @staticmethod
    def get_scheduled_live_info(youtube_url):
        # URLから動画IDを抽出
        parsed_url = urlparse(youtube_url)
        video_id = parse_qs(parsed_url.query).get("v")

        if not video_id:
            print("無効なURLです。動画IDが見つかりません。")
            return None

        video_id = video_id[0]

        # YouTube Data APIで動画情報を取得
        api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key=YOUR_API_KEY&part=snippet,liveStreamingDetails"
        response = requests.get(api_url)

        if response.status_code != 200:
            print(f"APIリクエストエラー: {response.status_code}")
            return None

        data = response.json()

        if "items" not in data or len(data["items"]) == 0:
            print("動画情報が見つかりません。")
            return None

        video_info = data["items"][0]["snippet"]
        live_info = data["items"][0].get("liveStreamingDetails", {})

        title = video_info["title"]
        live_broadcast_content = video_info["liveBroadcastContent"]

        # 配信予定のライブかどうかを確認
        if live_broadcast_content == "upcoming":
            scheduled_start_time_utc = live_info.get("scheduledStartTime")

            if scheduled_start_time_utc:
                # UTC時間をdatetimeオブジェクトに変換
                utc_time = datetime.strptime(
                    scheduled_start_time_utc, "%Y-%m-%dT%H:%M:%SZ"
                )
                utc_time = utc_time.replace(tzinfo=pytz.utc)

                # Asia/Tokyoタイムゾーンに変換
                tokyo_tz = pytz.timezone("Asia/Tokyo")
                scheduled_start_time_tokyo = utc_time.astimezone(tokyo_tz)

                # Googleカレンダーに追加
                event = {
                    "summary": title,
                    "description": youtube_url,
                    "start": {
                        "dateTime": scheduled_start_time_tokyo.isoformat(),
                        "timeZone": "Asia/Tokyo",
                    },
                    "end": {
                        "dateTime": scheduled_start_time_tokyo.isoformat(),
                        "timeZone": "Asia/Tokyo",
                    },
                    "reminders": {
                        "useDefault": False,
                        "overrides": [
                            {"method": "popup", "minutes": 1},
                            {"method": "popup", "minutes": 30},
                        ],
                    },
                }

                try:
                    creds = None

                    if os.path.exists("token.json"):
                        creds = Credentials.from_authorized_user_file("token.json")

                    if not creds or not creds.valid:
                        if creds and creds.expired and creds.refresh_token:
                            creds.refresh(Request())
                        else:
                            flow = InstalledAppFlow.from_client_secrets_file(
                                "credentials.json",
                                ["https://www.googleapis.com/auth/calendar.events"],
                            )
                            creds = flow.run_local_server(port=0)

                            with open("token.json", "w") as token:
                                token.write(creds.to_json())

                    service = build("calendar", "v3", credentials=creds)
                    event = (
                        service.events()
                        .insert(calendarId="primary", body=event)
                        .execute()
                    )
                    print(f'Event created: {event.get("htmlLink")}')
                except Exception as e:
                    print(f"Googleカレンダーへの追加中にエラーが発生しました: {str(e)}")
                    return None

                return title, scheduled_start_time_tokyo.isoformat()
            else:
                print("予定開始時間が見つかりません。")
                return None
        else:
            print(f"タイトル: {title}\nこの動画は配信予定のライブではありません。")


# ボットのクラス
# MyBotクラスの定義
class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents, config):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.config = config
        self.rss_urls = config.get("rss_urls", [])
        self.youtube_rss = config.get("youtube_rss", [])
        self.task_message_instance = (
            None  # TaskMessageインスタンスを保持するプロパティを追加
        )

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

        # TaskMessageのインスタンスを作成
        self.task_message_instance = TaskMessage(self)
        print("TaskMessage instance created.")
        self.task_message_instance.start()

        # コマンドの同期
        await self.tree.sync()
        print("Commands synchronized.")

        # コマンドの登録状態を確認する
        for command in self.tree.get_commands():
            print(f"Command: {command.name}")
        print("-------------------------")

        # ステータス設定
        activity = discord.Streaming(
            name="夏凪優羽がサポートするよ！！！",
            url="https://www.twitch.tv/shirafukayayoi",
        )
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
