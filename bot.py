import cgi
import codecs
import re
import feedparser as fp
import audioop
import aiohttp
import logging
import discord
from discord import User, ClientUser, Invite, Template
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    guild = discord.Object(id=int(os.getenv("SERVER_ID")))
    await bot.tree.sync(guild=guild)
    for cmd in bot.tree.get_commands():
        print(f"Registered command: {cmd.name}")
    print(f"{bot.user} has connected.")
        
async def load_extensions():
    await bot.load_extension("cogs.user_commands")
    
if __name__ == "__main__":
    import asyncio
    async def main():
        await load_extensions()
        await bot.start(TOKEN)
    asyncio.run(main())