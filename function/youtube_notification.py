import feedparser
import asyncio
import json
import os
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GoogleSpreadsheet:
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = Credentials.from_service_account_file('sheet_credentials.json', scopes=self.scope)
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open_by_key(os.environ["SPREADSHEET_KEY"])
        self.sheet = self.spreadsheet.sheet1  # 最初のシートにアクセス

    def write_data(self, data):
        self.sheet.append_row(data)
        print("データを書き込みました")

class YoutubeNotification:
    def __init__(self, bot):
        self.bot = bot
        self.google_spreadsheet = GoogleSpreadsheet()

    def load_youtube_rss_urls(self):
        """ config.json から YouTube の RSS フィードの URL を読み込む """
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return [item["url"] if isinstance(item, dict) else item for item in config.get("youtube_rss", [])]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading youtube_rss urls: {e}")
            return []

    def load_youtube_latest_entry_ids(self):
        """ config.json から最新のエントリーIDを読み込む """
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config.get("youtube_latest_entry_ids", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading youtube_latest_entry_ids: {e}")
            return {}

    def save_latest_entry_ids(self):
        """ 最新のエントリーIDを config.json に保存する """
        try:
            with open('config.json', 'r+') as f:
                config = json.load(f)
                config["youtube_latest_entry_ids"] = self.latest_entry_ids
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error saving youtube_latest_entry_ids: {e}")

    async def check_rss_feed(self):
        while not self.bot.is_closed():  # ボットが終了するまで繰り返す
            await self.send_message()  # RSSフィードを確認してメッセージを送信
            await asyncio.sleep(3600)  # 指定された時間ごとにRSSフィードをチェック

    async def send_message(self, notify_no_update=False):
        channel_id = int(os.environ["CHANNEL_ID"])
        channel = self.bot.get_channel(channel_id)

        self.rss_urls = self.load_youtube_rss_urls()  # YouTube RSS URL の読み込み
        self.latest_entry_ids = self.load_youtube_latest_entry_ids()  # 最新エントリー ID の読み込み
        has_new_content = False

        for rss_url in self.rss_urls:
            try:
                feed = feedparser.parse(rss_url)
                print(f"Checking {rss_url}...")  # デバッグ用ログ
                
                if feed.entries:

                    latest_entry = feed.entries[0]
                    last_entry_id = self.latest_entry_ids.get(rss_url)

                    if last_entry_id is None or last_entry_id != latest_entry.id:
                        self.latest_entry_ids[rss_url] = latest_entry.id

                        # `published` 属性の存在をチェック
                        published_str = getattr(latest_entry, 'published', '未知の公開日')
                        if published_str == '未知の公開日':
                            formatted_published = '公開日不明'
                        else:
                            try:
                                published_datetime = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
                                formatted_published = published_datetime.strftime("%Y/%m/%d %H:%M:%S")
                            except ValueError:
                                formatted_published = published_str  # 日付形式が異なる場合はそのまま表示

                        message = f"新しい動画が投稿されました！\n**{latest_entry.title}**\n`{formatted_published}`\n{latest_entry.link}"
                        self.google_spreadsheet.write_data([latest_entry.title, latest_entry.link, formatted_published])
                        await channel.send(message)
                        has_new_content = True

                        self.save_latest_entry_ids()
                else:
                    print(f"No entries found in {rss_url}")  # デバッグ用ログ

            except Exception as e:
                print(f"RSSフィードの処理中にエラーが発生しました: {e}")

        if notify_no_update and not has_new_content:
            print("最新の動画がないため通知しません")
            return "最新の動画がないよ！"
        return None

    def add_rss_url(self, url):
        if url not in self.rss_urls:
            self.rss_urls.append(url)
            self.latest_entry_ids[url] = None  # 新しいRSSのエントリーIDを初期化
            self.save_latest_entry_ids()
            return True
        return False
