import os
import asyncio
import json
import discord

class TaskMessage:
    def __init__(self, bot):
        self.bot = bot
        self.minute = self.load_config().get("minutes", 0)
        self.INTERVAL_SECONDS = self.minute * 60  # 秒単位に変換
        self.task = None  # asyncio タスクを管理するための変数
        print(f"TaskMessage: {self.INTERVAL_SECONDS}秒ごとにメッセージを送信します")

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("config.json が見つかりません。デフォルト設定を使用します。")
            return {"minutes": 0}
        except json.JSONDecodeError:
            print("config.json の読み込みに失敗しました。デフォルト設定を使用します。")
            return {"minutes": 0}

    async def send_message(self):
        channel_id = os.environ.get("TASKMESSAGE_ID")
        if not channel_id:
            print("CHANNEL_ID が設定されていません。メッセージを送信できません。")
            return

        channel = self.bot.get_channel(int(channel_id))
        if channel:
                try:
                    await channel.send("あんまりキツいこと言いたくないんだけど、言った方がいいと思ったから言うね\nヒゲと靴下と内股は直した方がいいと思うよ。\n清潔感大事っていう女子多いから、眉毛整えたりヒゲ剃ったりした方がいいかも。\n靴下は長いのぐしゃってやって履くとルーズソックスに見えるからやめたほうが…\nあと内股についてで、そう簡単に直せるもんじゃないと思うけど、ちょっと意識するだけでも変わると思うから頑張ってみて。\nこの前後輩に金丸先輩って内股なんですねって言われちゃってたから…\nちなみにこの後輩は金丸が好きな人じゃないよ。\nこんなこと言った私が言うのもあれなんだけど、後輩の事は疑ったり嫌ったりしないであげてね。")
                except discord.DiscordException as e:
                    print(f"メッセージ送信中にエラーが発生しました: {e}")
        else:
            print("指定されたチャンネルが見つかりません。メッセージを送信できません。")

    async def scheduled_task(self):
        await self.send_message()
        

    def start(self):
        if self.task is None:
            self.task = self.bot.loop.create_task(self.run())  # タスクを開始するメソッド

    def cancel(self):
        if self.task:
            self.task.cancel()  # タスクをキャンセル
            self.task = None

    async def run(self):
        while True:
            await self.scheduled_task()
            await asyncio.sleep(self.INTERVAL_SECONDS)  # 指定した間隔でスリープ
