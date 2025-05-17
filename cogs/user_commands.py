import discord
from discord import app_commands
from discord.ext import commands
from database.connection import AsyncSessionLocal
from database import crud
from cogs.feed_read import process
import logging

class UserCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="readzme", description="Register yourself with the bot")
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
                user = await crud.get_user(session=session, server_id=server.id, discord_id=user_id)
                if user:
                    await interaction.response.send_message(f"{username}, you're already registered!")
                    return
                await crud.create_user(
                    session=session,
                    server_id=server.id,
                    discord_id=user_id,
                    discord_username=username,
                    goodreads_user_id=goodreads_id,
                    goodreads_display_name=goodreads_display_name
                )
                await interaction.response.send_message(f"{username} ({goodreads_display_name}), you've been registered!")
            except Exception as e:
                logging.info(f"Error creating user in DB: {e}")
                await interaction.response.send_message("There was an error registering you. Please try again.", ephemeral=True)

    @app_commands.command(name="readznotme", description="Unregister yourself from the bot")
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
                user = await crud.get_user(session=session, server_id=server.server_id, discord_id=user_id)
                if not user:
                    await interaction.response.send_message(f"{username}, you're not registered!")
                    return
                await crud.delete_user(session=session, server_id=server.server_id, discord_id=user_id)
                await interaction.response.send_message(f"{username}, you've been removed!")
            except Exception as e:
                logging.info(f"Error fetching user from DB: {e}")
                await interaction.response.send_message("There was an error unregistering you. Please try again.", ephemeral=True)
                return
            
    @app_commands.command(name="updatereadz", description="Update feeds")
    async def update_readz(self, interaction: discord.Interaction):
        logging.info(f"Updating feeds for user: {interaction.user.name}")
        try:
            await process(server_id=interaction.guild.id)
            await interaction.response.send_message(f"Feeds update has been triggered!")
        except Exception as e:
            logging.info(f"Error updating feeds: {e}")
            await interaction.response.send_message("There was an error updating feeds. Please try again.", ephemeral=True)

async def setup(bot):
    logging.info("Loading commands from cogs.user_commands.py")
    await bot.add_cog(UserCommands(bot))
    