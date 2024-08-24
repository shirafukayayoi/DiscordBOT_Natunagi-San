import discord
from discord.ext import commands
import os
import json
from command.GoogleCalendarTemplate import CalendarPush
from function.task_message import TaskMessage
from typing import List
from discord import app_commands
from autocomplete.auto_playlist import autocomplete_playlist
from command.Gboard_Change import process_file
from autocomplete.auto_youtube_name import autocomplete_youtube
from command.YoutubeTemplate import YoutubeTemplate
from command.GoogleCalendarTemplate import YoutubePush

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

def setup(bot: commands.Bot):
    @bot.tree.command(name="hello", description="Says hello!")
    async def hello(interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

    @bot.tree.command(name='calendarpush', description='Googleカレンダーにイベントを追加します')
    async def calendarpush(interaction: discord.Interaction, eventname: str, eventdate: str):
        if len(eventdate) != 8 or not eventdate.isdigit():
            await interaction.response.send_message("日付は20240801のように入力してください")
            return

        try:
            calendarpush = CalendarPush(eventname, eventdate)
            await interaction.response.send_message(f"イベント名: `{eventname}`\n日付: `{eventdate}`\nを追加しました")
        except Exception as e:
            await interaction.response.send_message(f"エラーが発生しました: {e}")

    @bot.tree.command(name='rss-set', description='RSSフィードのURLを追加します')
    async def setrss(interaction: discord.Interaction, url: str):
        if bot.add_rss_url(url):
            await interaction.response.send_message(f"RSS URLが追加されました: {url}")
        else:
            await interaction.response.send_message(f"このRSS URLは既に追加されています。")

    @bot.tree.command(name='rss-list', description='登録されているRSSフィードのURLを表示します')
    async def listrss(interaction: discord.Interaction):
        if bot.rss_urls:
            url_list = "\n".join(bot.rss_urls)
            await interaction.response.send_message(f"登録されているRSS URLリスト:\n{url_list}")
        else:
            await interaction.response.send_message("現在、登録されているRSS URLはありません。")

    @bot.tree.command(name='rss-remove', description='登録されているRSSフィードのURLを削除します')
    async def removerss(interaction: discord.Interaction, url: str):
        if url in bot.rss_urls:
            bot.rss_urls.remove(url)
            bot.config["rss_urls"] = bot.rss_urls
            save_config(bot.config)
            await interaction.response.send_message(f"RSS URLが削除されました: {url}")
        else:
            await interaction.response.send_message(f"このRSS URLは登録されていません。")

    @bot.tree.command(name='rss-now', description='RSSの確認をします')
    async def rssnow(interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            await bot.rss_handler.send_message(notify_no_update=True)
            await interaction.followup.send("RSSの確認が完了しました。")
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {e}")
            print(f"エラー発生: {e}")

    @bot.tree.command(name='send-minute', description='指定した分数ごとにメッセージを送信するための時間を設定します')
    async def send_minute(interaction: discord.Interaction, minutes: int):
        global INTERVAL_MINUTES

        # 1. 分数の設定と保存
        INTERVAL_MINUTES = minutes
        bot.config["minutes"] = minutes
        save_config(bot.config)

        # 2. 既存のタスクインスタンスがあればキャンセル
        if bot.task_message_instance:
            bot.task_message_instance.cancel()

        # 3. 新しいタスクインスタンスを作成して開始
        bot.task_message_instance = TaskMessage(bot)
        bot.task_message_instance.start()

        await interaction.response.send_message(f"メッセージ送信間隔を{minutes}分に設定しました。")

    @bot.tree.command(name='summon-playlist', description='プレイリストを呼び出します')
    @app_commands.autocomplete(playlist=autocomplete_playlist)
    async def summon_playlist(interaction: discord.Interaction, playlist: str):
        if playlist == "とにかく詰め込め！":
            await interaction.response.send_message("https://youtube.com/playlist?list=PLHh1qLt2rZLK4QFgf_W0pZLAMSiipfT3o&si=pf23FQmirl2agzLt")
        elif playlist == "ブルーアーカイブOST":
            await interaction.response.send_message("https://youtube.com/playlist?list=PLh6Ws4Fpphfqr7VL72Q6HK5Ole9YI54hv&si=yL9IWx3zvuuw3YcP")

    @bot.tree.command(name='youtube-set-rss', description='YouTubeのRSSフィードのURLを追加します')
    async def youtube_setrss(interaction: discord.Interaction, name: str, url: str):
        if bot.add_youtube_rss_url(name, url):
            await interaction.response.send_message(f"RSS URLが追加されました:\n{name} - {url}")
        else:
            await interaction.response.send_message(f"このYouTube RSS URLは既に追加されています。")

    @bot.tree.command(name='youtube-list-rss', description='登録されているYouTubeのRSSフィードのURLを表示します')
    async def youtube_listrss(interaction: discord.Interaction):
        if bot.youtube_rss:
            url_list = "\n".join(f"{entry['name']}  {entry['url']}" for entry in bot.youtube_rss if isinstance(entry, dict))
            await interaction.response.send_message(f"登録されているYouTube RSS URLリスト:\n{url_list}")
        else:
            await interaction.response.send_message("現在、登録されているYouTube RSS URLはありません。")

    @bot.tree.command(name='youtube-remove-rss', description='登録されているYouTubeのRSSフィードのURLを削除します')
    @app_commands.autocomplete(name=autocomplete_youtube)
    async def remove_youtube_rss(interaction: discord.Interaction, name: str):
        entry_to_remove = None
        # youtube_rssから削除するエントリを探す
        for entry in bot.youtube_rss:
            if isinstance(entry, dict) and entry.get("name") == name:
                entry_to_remove = entry
                break
        
        if entry_to_remove:
            # youtube_rssからエントリを削除
            bot.youtube_rss.remove(entry_to_remove)
            
            # youtube_latest_entry_idsから対応するURLを削除
            url_to_remove = entry_to_remove["url"]
            if url_to_remove in bot.config["youtube_latest_entry_ids"]:
                del bot.config["youtube_latest_entry_ids"][url_to_remove]
            
            # 設定を保存
            bot.config["youtube_rss"] = bot.youtube_rss
            save_config(bot.config)
            
            await interaction.response.send_message(f"RSS URLが削除されました: {name} - {entry_to_remove['url']}")
        else:
            await interaction.response.send_message(f"指定された名前のRSSフィードが見つかりませんでした: {name}")
    
    @bot.tree.command(name='youtube-now', description='YouTubeのRSSの確認をします')
    async def youtube_now(interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            await bot.youtube_notification.send_message(notify_no_update=True)
            await interaction.followup.send("YouTube RSSの確認が完了しました。")
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {e}")
            print(f"エラー発生: {e}")
    
    @bot.tree.command(name='youtube-push', description='Youtubeの通知をGoogleカレンダーに追加します')
    async def youtube_push(interaction: discord.Interaction, youtube_url: str):
        await interaction.response.defer()

        try:
            youtubepush = YoutubeTemplate(youtube_url)
            result = youtubepush.get_scheduled_live_info()

            if not result:
                raise ValueError("ライブ配信情報が取得できませんでした")

            title, scheduled_start_time_tokyo = result

            googlepush = YoutubePush(title, scheduled_start_time_tokyo, youtube_url)
            if not interaction.response.is_done():
                await interaction.followup.send(f"タイトル: `{title}`\n予定開始時間 (Asia/Tokyo): `{scheduled_start_time_tokyo}`\nを追加しました\nURL: {youtube_url}")

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.followup.send(f"エラーが発生しました: {str(e)}")
            else:
                # レスポンスがすでに送信された後にエラーが発生した場合はログに記録する
                print(f"エラーが発生しましたが、メッセージは既に送信されています: {str(e)}")

    @bot.tree.command(name='remove-text', description='指定したユーザーのメッセージを削除します')
    async def remove_text(interaction: discord.Interaction, user: discord.User, limit: int):
        if limit > 50:
            await interaction.response.send_message("50以下にして！！！")
            return

        await interaction.response.defer()

        async for message in interaction.channel.history(limit=limit):
            if message.author == user:
                await message.delete()

    @bot.tree.command(name="gboard-change", description="gboardの言語をja-JPに変換します")
    async def gboard_change(interaction: discord.Interaction, file: discord.Attachment):
        try:
            # process_file 関数を await で呼び出す
            zip_file_name = await process_file(file)
            await interaction.response.send_message(
                content="ファイルを変換しました",
                file=discord.File(zip_file_name)
            )
            
            # zipファイルの削除
            os.remove(zip_file_name)
            
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message("エラーが発生しました")
