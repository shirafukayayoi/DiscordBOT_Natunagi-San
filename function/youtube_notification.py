import feedparser
import asyncio
import os
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GoogleSpreadsheet:
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
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
        self.rss_urls = bot.youtube_rss
        self.latest_entry_ids = {}  # 各RSSの最新のIDを格納する辞書
        self.google_spreadsheet = GoogleSpreadsheet()
    
    async def check_rss_feed(self):
        channel_id = int(os.environ["CHANNEL_ID"])
        channel = self.bot.get_channel(channel_id)
    
        first_run = True  # 初回の実行フラグ
    
        while not self.bot.is_closed():  # ボットが終了するまで繰り返す
            if not first_run:  # 初回の実行ではない場合のみ処理を行う
                for rss_url in self.rss_urls:  # 登録されているRSS URLを1つずつ処理
                    try:
                        feed = feedparser.parse(rss_url)  # RSSフィードを取得
                        if feed.entries:
                            latest_entry = feed.entries[0]
                            last_entry_id = self.latest_entry_ids.get(rss_url)
    
                            # 新しいエントリーがあれば、メッセージを送信
                            if last_entry_id != latest_entry.id:
                                self.latest_entry_ids[rss_url] = latest_entry.id
                                
                                # 日付を整形する
                                # '2024-08-16T19:23:16+00:00' -> '2024/08/16 19:23:16'
                                published_datetime = datetime.strptime(latest_entry.published, "%Y-%m-%dT%H:%M:%S%z")
                                formatted_published = published_datetime.strftime("%Y/%m/%d %H:%M:%S")
    
                                message = f"新しい動画が投稿されました！\n**{latest_entry.title}**\n`{formatted_published}`\n{latest_entry.link}"
                                self.google_spreadsheet.write_data([formatted_published, latest_entry.title, latest_entry.link])
                                await channel.send(message)
                    except Exception as e:
                        print(f"RSSフィードの処理中にエラーが発生しました: {e}")
            else:
                first_run = False  # 初回の実行フラグをオフにする
            await asyncio.sleep(3600)
            # 1時間ごとにRSSフィードをチェック
            await asyncio.sleep(3600)

    def add_rss_url(self, url):
        if url not in self.rss_urls:
            self.rss_urls.append(url)
            self.latest_entry_ids[url] = None
            return True
        return False