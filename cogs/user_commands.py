import discord
from discord import app_commands
from discord.ext import commands
from database.connection import AsyncSessionLocal
from database import crud
from cogs.feed_read import process
import logging

from dotenv import load_dotenv
import os

load_dotenv()

SERVER_ID = int(os.getenv("SERVER_ID"))

class UserCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="readzme", description="Register yourself with the bot")
    @app_commands.guilds(discord.Object(id=SERVER_ID))
    async def readzme(self, interaction: discord.Interaction, goodreads_profile_url: str):
        server_id = interaction.guild.id
        user_id = interaction.user.id
        username = interaction.user.name
        goodreads_user_data = goodreads_profile_url.split("/")[-1]
        goodreads_id = goodreads_user_data.split("-")[0]
        goodreads_display_name = goodreads_user_data.split("-")[1]
        logging.info(f"Registering user: {username} with ID: {user_id} from server: {server_id} and Goodreads id: {goodreads_id} and display name: {goodreads_display_name}")
        
        async with AsyncSessionLocal() as session:
            try:
                server = await crud.get_server_by_server_id(session=session, server_id=server_id)
                if not server:
                    await interaction.response.send_message("Server not found in the database. Please contact an admin.", ephemeral=True)
                    return
                user = await crud.get_user(session=session, server_id=server.server_id, user_id=user_id)
                if user:
                    await interaction.response.send_message(f"{username}, you're already registered!")
                    return
                await crud.create_user(
                    session=session,
                    server_id=server.server_id,
                    user_id=user_id,
                    discord_username=username,
                    goodreads_user_id=goodreads_id,
                    goodreads_display_name=goodreads_display_name
                )
                await interaction.response.send_message(f"{username} ({goodreads_display_name}), you've been registered!")
            except Exception as e:
                logging.info(f"Error creating user in DB: {e}")
                await interaction.response.send_message("There was an error registering you. Please try again.", ephemeral=True)

    @app_commands.command(name="readznotme", description="Unregister yourself from the bot")
    @app_commands.guilds(discord.Object(id=SERVER_ID))
    async def readznotme(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        user_id = interaction.user.id
        username = interaction.user.name
        logging.info(f"Unregistering user: {username} with ID: {user_id} from server: {server_id}")
        async with AsyncSessionLocal() as session:
            try:
                server = await crud.get_server_by_server_id(session=session, server_id=server_id)
                if not server:
                    await interaction.response.send_message("Server not found in the database. Please contact an admin.", ephemeral=True)
                    return
                user = await crud.get_user(session=session, server_id=server.server_id, user_id=user_id)
                if not user:
                    await interaction.response.send_message(f"{username}, you're not registered!")
                    return
                await crud.delete_user(session=session, server_id=server.server_id, user_id=user_id)
                await interaction.response.send_message(f"{username}, you've been removed!")
            except Exception as e:
                logging.info(f"Error fetching user from DB: {e}")
                await interaction.response.send_message("There was an error unregistering you. Please try again.", ephemeral=True)
                return
            
    @app_commands.command(name="updatereadz", description="Update feeds")
    @app_commands.guilds(discord.Object(id=SERVER_ID))
    async def updatereadz(self, interaction: discord.Interaction):
        logging.info(f"Updating feeds for user: {interaction.user.name}")
        try:
            await process(self.bot, server_id=interaction.guild.id)
            await interaction.response.send_message(f"Feeds update has been triggered!")
        except Exception as e:
            logging.info(f"Error updating feeds: {e}")
            await interaction.response.send_message("There was an error updating feeds. Please try again.", ephemeral=True)
       
    # 🛑 This command is currently deprecated in favor of `/setup_forum`
    # Uncomment down the line to re-enable text channel routing support
    
    # @app_commands.command(name="setchannel", description="Set the channel for bot notifications.")
    # @app_commands.describe(channel="Select a text or forum channel for bot messages")
    # async def setchannel(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel = None):
    #     target_channel = channel or interaction.channel

    #     # Only allow Text or Forum channels
    #     if not isinstance(target_channel, (discord.TextChannel, discord.ForumChannel)):
    #         await interaction.response.send_message("❌ Please select a text or forum channel.", ephemeral=True)
    #         return

    #     channel_type = "forum" if isinstance(target_channel, discord.ForumChannel) else "text"

    #     async with AsyncSessionLocal() as session:
    #         await crud.set_notification_channel(
    #             session,
    #             server_id=interaction.guild.id,
    #             channel_id=target_channel.id,
    #             channel_type=channel_type
    #         )

    #     await interaction.response.send_message(
    #         f"✅ Bot messages will be sent to {target_channel.mention} ({channel_type}).",
    #         ephemeral=True
    #     )
    
    @app_commands.command(name="setup_forum", description="Create and register bot threads in a forum channel.")
    @app_commands.describe(
        forum_channel="The forum channel to set up with Polls and Updates threads"
    )
    @app_commands.guilds(discord.Object(id=SERVER_ID))
    async def setup_forum(
        self,
        interaction: discord.Interaction,
        forum_channel: discord.ForumChannel
    ):
        if not isinstance(forum_channel, discord.ForumChannel):
            await interaction.response.send_message("❌ Please select a valid forum channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            registered_threads = {}

            for thread_type, thread_name in {
                "poll": "📊 Polls & Voting",
                "update": "📣 Reading Updates"
            }.items():
                thread = await find_existing_thread(interaction.guild, forum_channel, thread_name)
                
                if not thread:
                    created_thread = await forum_channel.create_thread(
                        name=thread_name,
                        content=f"Created by {self.bot.user.display_name} to handle `{thread_type}` posts.",
                    )
                    thread = created_thread.thread
                    
                await crud.set_forum_thread(session, interaction.guild.id, thread_type, thread.id)
                registered_threads[thread_type] = thread

            await crud.set_notification_channel(
                session,
                server_id=interaction.guild.id,
                channel_id=forum_channel.id,
                channel_type="forum"
            )

        await interaction.followup.send(
            "✅ Setup complete!\n\n" +
            "\n".join(f"• `{t}` thread: {th.mention}" for t, th in registered_threads.items()),
            ephemeral=True
        )
        
    @app_commands.command(name="current_setup", description="Show the bot's current channel and thread configuration")
    @app_commands.guilds(discord.Object(id=SERVER_ID))
    async def current_setup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        server_id = interaction.guild.id
        bot = self.bot

        async with AsyncSessionLocal() as session:
            settings = await crud.get_notification_channel(session, server_id)
            threads = await crud.get_all_forum_threads(session, server_id)

        embed = discord.Embed(title="📋 Current Bot Setup", color=discord.Color.blurple())

        # Forum-based config
        if settings and settings.channel_type == "forum":
            forum_channel = bot.get_channel(settings.channel_id)
            embed.add_field(name="Forum Channel", value=forum_channel.mention if forum_channel else "⚠️ Not found", inline=False)

            if threads:
                for thread_type in ["poll", "update"]:
                    thread_id = threads.get(thread_type)
                    thread_obj = bot.get_channel(thread_id) if thread_id else None
                    name = {
                        "poll": "📊 Polls Thread",
                        "update": "📣 Updates Thread"
                    }.get(thread_type, thread_type.capitalize())
                    embed.add_field(
                        name=name,
                        value=thread_obj.mention if thread_obj else "⚠️ Not set",
                        inline=False
                    )
            else:
                embed.add_field(name="Forum Threads", value="⚠️ No threads registered.\nUse `/setup_forum` or `/setthread`.", inline=False)

        # Text-channel fallback config
        elif settings and settings.channel_type == "text":
            channel = bot.get_channel(settings.notification_channel_id)
            embed.add_field(name="Text Channel", value=channel.mention if channel else "⚠️ Not found", inline=False)

        else:
            embed.description = "⚠️ No notification channel is currently configured.\nUse `/setup_forum` or `/setchannel` to configure one."

        await interaction.followup.send(embed=embed, ephemeral=True)
        
    

async def setup(bot):
    logging.info("Loading commands from cogs.user_commands.py")
    await bot.add_cog(UserCommands(bot))
    
async def find_existing_thread(guild: discord.Guild, forum_channel: discord.ForumChannel, name: str) -> discord.Thread | None:
    for thread in guild.threads:
        print(f"Checking thread: {thread.name.strip().lower()} with parent_id {thread.parent_id} against channel {forum_channel.name} with id {forum_channel.id} - comparing with thread: {name.strip().lower()}")
        if thread.parent_id == forum_channel.id and thread.name.strip().lower() == name.strip().lower():
            return thread
    return None
    