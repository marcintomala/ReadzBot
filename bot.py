import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from database.connection import AsyncSessionLocal
import database.crud as crud
from database.models import Server, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    server_id = int(os.getenv("SERVER_ID"))
    guild = bot.get_guild(server_id)
    synced = await bot.tree.sync(guild=guild)
    for cmd in bot.tree.get_commands():
        logging.info(f"Registered command: {cmd.name}")
    logging.info(f"{bot.user} has connected.")
    async with AsyncSessionLocal() as session:
        existing_server_ids = [server.server_id for server in await crud.get_all_servers(session)]
        for guild in bot.guilds:
            if guild.id not in existing_server_ids:
                new_server = Server(server_id=guild.id, server_name=guild.name)
                session.add(new_server)
                await session.commit()
                logging.info(f"Added new server to DB: {guild.name} ({guild.id})")
            else:
                logging.info(f"Server already exists in DB: {guild.name} ({guild.id})")
    print("Synced commands:")
    for cmd in synced:
        print(f" - {cmd.name}")
        
@bot.event
async def on_guild_join(guild):
    async with AsyncSessionLocal() as session:
        existing_server_ids = [server.id for server in await crud.get_all_servers(session)]
        if guild.id not in existing_server_ids:
            new_server = Server(server_id=guild.id, server_name=guild.name)
            session.add(new_server)
            await session.commit()
            logging.info(f"Added new server to DB: {guild.name} ({guild.id})")
        else:
            logging.info(f"Server already exists in DB: {guild.name} ({guild.id})")
        
async def load_extensions():
    await bot.load_extension("cogs.user_commands")
    await bot.load_extension("cogs.scheduler")
    
async def run_discord_bot():
    await init_db()
    await load_extensions()
    await bot.start(TOKEN)