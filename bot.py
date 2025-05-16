import cgi
import codecs
import re
import feedparser as fp
import audioop
import aiohttp
import asyncio
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
    print(f"{bot.user} has connected.")
    
        # Replace with your channel ID
    channel_id = os.getenv("CHANNEL")
    channel = bot.get_channel(channel_id)

    if channel:
        await channel.send("Hello from the bot!")
    else:
        print("Channel not found or bot lacks access.")

bot.run(TOKEN)