import discord
from discord import app_commands
import json
from typing import List

async def autocomplete_youtube(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    # config.jsonを読み込む
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)

    # youtube_rss の name のリストを作成する
    fruits = [entry['name'] for entry in config['youtube_rss'] if isinstance(entry, dict)]

    choices = []
    playlist = interaction.data.get("options")[0].get("value")
    for fruit in fruits:
        if playlist.lower() in fruit.lower():
            choices.append(app_commands.Choice(name=fruit, value=fruit))
    return choices
