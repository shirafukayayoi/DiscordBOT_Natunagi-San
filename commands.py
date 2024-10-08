import discord
from discord.ext import commands
import os
import json
from command.GoogleCalendarTemplate import CalendarPush
from function.task_message import TaskMessage
from typing import List
from discord import app_commands
from autocomplete.auto_playlist import autocomplete_playlist
from autocomplete.auto_get_SpreadSheet import autocomplete_getspreadsheet
from command.Gboard_Change import process_file
from autocomplete.auto_youtube_name import autocomplete_youtube
from command.YoutubeTemplate import YoutubeTemplate
from command.GoogleCalendarTemplate import YoutubePush
from command.youtube_download import YoutubeDownload
from command.Novel_Sale_List import get_novel_data
from command.Novel_Sale_List import get_manga_data
from command.Bookwalker_get_salelist import get_spreadsheet

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

    @bot.tree.command(name='rss-set', description='RSSフィードのURLを追加します')
    async def setrss(interaction: discord.Interaction, url: str):
        if bot.add_rss_url(url):
            await interaction.response.send_message(f"RSS URLが追加されました: {url}")
        else:
            await interaction.response.send_message(f"このRSS URLは既に追加されています。")

    @bot.tree.command(name='rss-list', description='登録されているRSSフィードのURLを表示します')
    async def listrss(interaction: discord.Interaction):
        embed = discord.Embed(title="登録されているRSSフィードのURLリスト",color=discord.Color.dark_gray())
        for url in bot.rss_urls:
            embed.add_field(
                name=url,
                value="",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

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
            result_message = await bot.rss_handler.send_message(notify_no_update=True)
            await interaction.followup.send(result_message)
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
        embed = discord.Embed(title="登録されているYouTube RSSフィードのURLリスト",color=discord.Color.red())
        for entry in bot.youtube_rss:
            embed.add_field(
                name=entry["name"],
                value=entry["url"],
                inline=False
            )

        await interaction.response.send_message(embed=embed)

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
            # メッセージの送信
            result_message = await bot.youtube_notification.send_message(notify_no_update=True)

            if result_message:
                await interaction.followup.send(result_message)
            else:
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
            await interaction.followup.send(f"タイトル: `{title}`\n予定開始時間 (Asia/Tokyo): `{scheduled_start_time_tokyo}`\nを追加しました\nURL: {youtube_url}")

        except Exception as e:
                await interaction.followup.send(f"エラーが発生しました: {str(e)}")
                # レスポンスがすでに送信された後にエラーが発生した場合はログに記録する
                print(f"エラーが発生しましたが、メッセージは既に送信されています: {str(e)}")
    
    @bot.tree.command(name='youtube-download', description='Youtubeの動画をダウンロードします')
    async def youtube_download(interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        try:
            file_path, title = await YoutubeDownload(url)

            # ファイルサイズを確認する
            file_size = os.path.getsize(file_path)
            max_size_mb = 50  # 最大ファイルサイズ (MB)
            max_size_bytes = max_size_mb * 1024 * 1024  # バイト単位に変換

            if file_size > max_size_bytes:
                await interaction.followup.send("ファイルが大きすぎます")
            else:
                await interaction.followup.send(
                    content=f"ダウンロード完了:\n**{title}**",
                    file=discord.File(file_path)
                )
            
            # ダウンロード後にファイルを削除
            os.remove(file_path)
        
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {str(e)}")

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

    @bot.tree.command(name="novel-moneylist", description="登録しているラノベの金額を表示します")
    async def novel_moneylist(interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            novel_data = get_novel_data()
            if not novel_data:
                await interaction.followup.send("データがありません")
            else:
                embed = discord.Embed(title="ラノベ金額一覧", color=discord.Color.blue())
                
                for title, url, total, sum in novel_data:
                    # URLをマークダウン記法でリンクにする
                    link = f"[Link]({url})"
                    # Embedに各小説の情報を追加
                    embed.add_field(
                        name=title,
                        value=f"金額: {sum} / 巻数: {total} / {link}",
                        inline=False
                    )
                
                # Embedを送信
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {str(e)}")

    @bot.tree.command(name="manga-moneylist", description="登録している漫画の金額を表示します")
    async def manga_moneylist(interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            novel_data = get_manga_data()
            if not novel_data:
                await interaction.followup.send("データがありません")
            else:
                embed = discord.Embed(title="漫画金額一覧", color=discord.Color.blue())
                
                for title, url, total, sum in novel_data:
                    # URLをマークダウン記法でリンクにする
                    link = f"[Link]({url})"
                    # Embedに各小説の情報を追加
                    embed.add_field(
                        name=title,
                        value=f"金額: {sum} / 巻数: {total} / {link}",
                        inline=False
                    )
                
                # Embedを送信
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {str(e)}")
    
    @bot.tree.command(name="bookwalker-salelist", description="Googleドライブに保存されているBOOKWALKERのセール情報を表示します")
    @app_commands.autocomplete(salelist=autocomplete_getspreadsheet)
    async def bookwalker_salelist(interaction: discord.Interaction, salelist: str):
        await interaction.response.defer()
        try:
            spreadsheets = get_spreadsheet(os.getenv('BOOKWALKER_FOLDER_ID'))

            if spreadsheets:
                # 一致するスプレッドシートを検索
                matching_spreadsheet = None
                salelist_clean = salelist.strip()  # salelist の前後の空白を削除
                for item in spreadsheets:
                    item_name_clean = item['name'].strip()  # item['name'] の前後の空白を削除
                    if item_name_clean == salelist_clean:
                        matching_spreadsheet = item
                        break

                if matching_spreadsheet:
                    url = f"https://docs.google.com/spreadsheets/d/{matching_spreadsheet['id']}"
                    await interaction.followup.send(f"これがセール情報のファイルだよ！！:\n{url}")
                else:
                    await interaction.followup.send("該当するセール情報が見つかりませんでした")
            else:
                await interaction.followup.send("スプレッドシートが見つかりませんでした")
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {str(e)}")
            print(f"エラー発生: {e}")
