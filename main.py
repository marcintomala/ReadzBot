import asyncio
import bot
import web

async def main():
    await asyncio.gather(
        bot.run_discord_bot(),    # Connects to Discord, handles RSS, etc.
        web.start_web_server()    # FastAPI ping route to keep the web service alive
    )

if __name__ == "__main__":
    asyncio.run(main())