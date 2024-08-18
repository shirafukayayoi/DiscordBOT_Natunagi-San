import discord
from discord import app_commands
from typing import List

async def autocomplete_playlist(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    fruits = ["とにかく詰め込め！", "ブルーアーカイブOST"]
    choices = []
    playlist = interaction.data.get("options")[0].get("value")
    for fruit in fruits:
        if playlist.lower() in fruit.lower():
            choices.append(app_commands.Choice(name=fruit, value=fruit))
    return choices
