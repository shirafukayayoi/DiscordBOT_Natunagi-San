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
        print("Google Spreadsheetに接続しました")

    def write_data(self, data):
        self.sheet.append_row(data)
        print("データを書き込みました")

class YoutubeNotification:
    def __init__(self, bot):
        self.bot = bot
        self.rss_urls = bot.config.get("rss_urls", [])
        
        # config.json から latest_entry_ids を読み込む
        self.latest_entry_ids = self.load_latest_entry_ids()

        self.check_interval = bot.config.get("minutes", 60) * 60  # 分を秒に変換

        # GoogleSpreadsheetのインスタンスを作成
        self.google_spreadsheet = GoogleSpreadsheet()

    def load_latest_entry_ids(self):
        """ config.json から最新のエントリーIDを読み込む """
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config.get("latest_entry_ids", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_latest_entry_ids(self):
        """ 最新のエントリーIDを config.json に保存する """
        try:
            with open('config.json', 'r+') as f:
                config = json.load(f)
                config["latest_entry_ids"] = self.latest_entry_ids
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error saving latest_entry_ids: {e}")

    async def check_rss_feed(self):
        while not self.bot.is_closed():  # ボットが終了するまで繰り返す
            await self.send_message()  # RSSフィードを確認してメッセージを送信
            await asyncio.sleep(self.check_interval)  # 指定された時間ごとにRSSフィードをチェック

    async def send_message(self, notify_no_update=False):   # コマンドからの呼び出しの場合は notify_no_update=True
        channel_id = int(os.environ["CHANNEL_ID"])
        channel = self.bot.get_channel(channel_id)

        has_new_content = False # 新しい記事があるかどうかの確認

        for rss_url in self.rss_urls:  # 登録されているRSS URLを1つずつ処理
            try:
                feed = feedparser.parse(rss_url)  # RSSフィードを取得
                
                if feed.entries:
                    latest_entry = feed.entries[0]
                    last_entry_id = self.latest_entry_ids.get(rss_url)

                    # 新しいエントリーがあれば、メッセージを送信
                    if last_entry_id is None or last_entry_id != latest_entry.id:
                        self.latest_entry_ids[rss_url] = latest_entry.id
                        
                        # 日付を整形する
                        published_datetime = datetime.strptime(latest_entry.published, "%Y-%m-%dT%H:%M:%S%z")
                        formatted_published = published_datetime.strftime("%Y/%m/%d %H:%M:%S")
                        
                        message = f"新しい動画が投稿されました！\n**{latest_entry.title}**\n`{formatted_published}`\n{latest_entry.link}"
                        self.google_spreadsheet.write_data([latest_entry.title, latest_entry.link, formatted_published])
                        await channel.send(message)
                        has_new_content = True  # 通知があったためtrueにする
                        
                        # 最新のIDを config.json に保存
                        self.save_latest_entry_ids()
            except Exception as e:
                print(f"RSSフィードの処理中にエラーが発生しました: {e}")

        # 最新の記事がなかった場合の通知
        if notify_no_update and not has_new_content:    # コマンドからの呼び出しで、新しい記事がなかった場合
            await channel.send("最新の動画がないよ！！")
            print("最新の動画がないため通知しません")
            
    def add_rss_url(self, url):
        if url not in self.rss_urls:
            self.rss_urls.append(url)
            self.latest_entry_ids[url] = None  # 新しいRSSのエントリーIDを初期化
            
            # 新しいURLが追加された場合、config.jsonに保存
            self.save_latest_entry_ids()
            return True
        return False
