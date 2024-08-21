import feedparser
import asyncio
import json
import os

class RSSHandler:
    def __init__(self, bot):
        self.bot = bot
        self.rss_urls = bot.config["rss_urls"]
        
        # config.json から latest_entry_ids を読み込む
        self.latest_entry_ids = self.load_latest_entry_ids()

        self.check_interval = bot.config.get("minutes", 60) * 60  # 分を秒に変換

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
                print(f"checking {rss_url}...")
                
                if feed.entries:
                    latest_entry = feed.entries[0]
                    last_entry_id = self.latest_entry_ids.get(rss_url)

                    # 新しいエントリーがあれば、メッセージを送信
                    if last_entry_id is None or last_entry_id != latest_entry.id:
                        self.latest_entry_ids[rss_url] = latest_entry.id
                        message = f"新しい記事が投稿されました！\n**{latest_entry.title}**\n{latest_entry.link}"
                        await channel.send(message)
                        has_new_content = True  # 通知があったためtrueにする
                        
                        # 最新のIDを config.json に保存
                        self.save_latest_entry_ids()
            except Exception as e:
                print(f"RSSフィードの処理中にエラーが発生しました: {e}")

        # 最新の記事がなかった場合の通知
        if notify_no_update and not has_new_content:    # コマンドからの呼び出しで、新しい記事がなかった場合
            await channel.send("最新の記事がないよ！！")
            print("最新の記事がないため通知しませんでした")
            
    def add_rss_url(self, url):
        if url not in self.rss_urls:
            self.rss_urls.append(url)
            self.latest_entry_ids[url] = None  # 新しいRSSのエントリーIDを初期化
            
            # 新しいURLが追加された場合、config.jsonに保存
            self.save_latest_entry_ids()
            return True
        return False
