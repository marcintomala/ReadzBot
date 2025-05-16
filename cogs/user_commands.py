import discord
from discord import app_commands
from discord.ext import commands
from database import crud

class UserCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="readzme", description="Register yourself with the bot")
    async def readzme(self, interaction: discord.Interaction, goodreads_profile_url: str):
        user_id = interaction.user.id
        username = interaction.user.name
        goodreads_user_data = goodreads_profile_url.split("/")[-1]
        goodreads_id = goodreads_user_data.split("-")[0]
        goodreads_display_name = goodreads_user_data.split("-")[1]
        print(f"Registering user: {username} with ID: {user_id} and Goodreads id: {goodreads_id} and display name: {goodreads_display_name}")
        try:
            crud.create_user(
                discord_id=user_id,
                discord_username=username,
                goodreads_user_id=goodreads_id,
                goodreads_display_name=goodreads_display_name
            )
            await interaction.response.send_message(f"{username} ({goodreads_display_name}), you've been registered!")
        except Exception as e:
            print(f"Error creating user in DB: {e}")
            await interaction.response.send_message("There was an error registering you. Please try again.", ephemeral=True)
            return

    @app_commands.command(name="readznotme", description="Unregister yourself from the bot")
    async def readznotme(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = interaction.user.name
        print(f"Unregistering user: {username} with ID: {user_id}")
        try:
            crud.delete_user(discord_id=user_id)
            await interaction.response.send_message(f"{username}, you've been removed!")
        except Exception as e:
            print(f"Error deleting user from DB: {e}")
            await interaction.response.send_message("There was an error unregistering you. Please try again.", ephemeral=True)

async def setup(bot):
    print("Loading commands from cogs.user_commands.py")
    await bot.add_cog(UserCommands(bot))