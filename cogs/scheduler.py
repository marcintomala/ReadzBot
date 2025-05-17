from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cogs.feed_read import process
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()

class SchedulerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.update_feed, 'interval', minutes=int(os.getenv("SCHEDULER_INTERVAL_MINUTES", 15)))
        self.scheduler.start()

    async def update_feed(self):
        logging.info("Updating feeds for all servers...")
        await process()
        logging.info("All feeds updated.")

async def setup(bot):
    logging.info("Starting scheduler...")
    await bot.add_cog(SchedulerCog(bot))
