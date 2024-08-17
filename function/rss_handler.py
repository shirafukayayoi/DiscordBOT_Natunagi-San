import feedparser
import asyncio
import os

class RSSHandler:
    def __init__(self, bot):
        self.bot = bot
        self.rss_urls = bot.rss_urls
        self.latest_entry_ids = {}  # 各RSSの最新のIDを格納する辞書

    async def check_rss_feed(self):
        channel_id = int(os.environ["RSS_CHANNEL_ID"])
        channel = self.bot.get_channel(channel_id)

        while not self.bot.is_closed(): # ボットが終了するまで繰り返す
            for rss_url in self.rss_urls:   # 登録されているRSS URLを1つずつ処理
                try:
                    feed = feedparser.parse(rss_url)    # RSSフィードを取得
                    if feed.entries:
                        latest_entry = feed.entries[0]
                        last_entry_id = self.latest_entry_ids.get(rss_url)

                        # 新しいエントリーがあれば、メッセージを送信
                        if last_entry_id != latest_entry.id:
                            self.latest_entry_ids[rss_url] = latest_entry.id
                            message = f"新しい記事が投稿されました！\n{latest_entry.title}\n{latest_entry.link}"
                            await channel.send(message)
                except Exception as e:
                    print(f"RSSフィードの処理中にエラーが発生しました: {e}")

            # 60秒ごとにチェック
            await asyncio.sleep(60)

    def add_rss_url(self, url):
        if url not in self.rss_urls:
            self.rss_urls.append(url)
            self.latest_entry_ids[url] = None  # 新しいRSSのエントリーIDを初期化
            return True
        return False
