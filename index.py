import discord
from discord import app_commands
from command.GoogleCalendarTemplate import CalendarMain
import os

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print('Commands synced.')

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

        # コマンドの登録状態を確認する
        for command in self.tree.get_commands():
            print(f'Command: {command.name}')
        print('------')
        activity = discord.Streaming(name="夏凪優羽がサポートするよ！！！", url="https://x.com/shirafuka_yayoi")
        await self.change_presence(status=discord.Status.online, activity=activity)

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

# スラッシュコマンドの定義
@client.tree.command(name="hello", description="Says hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

@client.tree.command(name='calendarpush', description='Googleカレンダーにイベントを追加します')
async def greet(interaction: discord.Interaction, eventname: str, eventdate: str):
    if len(eventdate) != 8 or not eventdate.isdigit():
        await interaction.response.send_message("日付は20240801のように入力してください")
        return

    # 特定の関数を呼び出し、引数を渡す
    CalendarPush = CalendarMain(eventname, eventdate)
    await interaction.response.send_message(f"イベント名: `{eventname}`\n日付: `{eventdate}`\nを追加しました")


client.run(os.environ['TOKEN'])
