import discord
from discord.ext import commands
import datetime as dt
from collections import defaultdict
from cogs.FeedEntry import FeedEntry

GOODREADS_BOOK_URL_STUB = 'https://www.goodreads.com/book/show/'

async def send_update_message(bot: commands.Bot, thread_id: int, user_id: int, entries: list[dict]):
    """
    Sends a feed update message to the appropriate 'update' thread for a given server.
    Requires the bot instance, server ID, and a parsed feed entry.
    """
    
    thread = bot.get_channel(thread_id)
    emojis = thread.guild.emojis
        
    user = await bot.fetch_user(user_id)

    if thread is None:
        print(f"⚠️ Thread ID {thread_id} not found in bot cache.")
        return

    embed = build_batch_feed_update_embed(entries, emojis, user)
    await thread.send(embed=embed)

def build_batch_feed_update_embed(entries: list[FeedEntry], emojis: tuple, user: discord.User) -> discord.Embed:
    """
    Build a single embed for multiple book updates.
    `entries` is a list of dicts with keys like:
        - title, author, link, user_shelves, rating
    """

    embed = discord.Embed(
        title=f'{discord.utils.get(emojis, name="applecat")} Goodreads Update',
        description=f'{discord.utils.get(emojis, name="RonaldoPog")} {user.mention} updated their shelves!',
        color=discord.Colour.blue(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )

    # Group by shelf
    grouped = defaultdict(list)
    
    for e in entries:
        grouped[e.shelf].append(e)
        print(f"Grouped {e.title} under shelf {e.shelf}")
        
    SHELF_ORDER = ['to-read', 'currently-reading', 'read']

    for shelf in SHELF_ORDER:
        if shelf not in grouped:
            continue
        books = grouped[shelf]
        lines = []
        for b in books:
            line = f"• [{b.title}]({GOODREADS_BOOK_URL_STUB}{b.book_id}) by {b.author}"
            if int(b.rating) > 0 and shelf == "read":
                stars = render_stars(int(b.rating))
                line += f" – {stars}"
            if b.review:
                line += f"\n> {b.review}"
            lines.append(line)

        pretty_shelf = {
            "to-read": "📚 To Read",
            "currently-reading": "📘 Currently Reading",
            "read": "✅ Read"
        }.get(shelf, shelf.capitalize())

        embed.add_field(name=pretty_shelf, value="\n".join(lines), inline=False)

    return embed

def render_stars(rating: int | float, max_stars: int = 5) -> str:
    """
    Convert a numeric rating (1-5) to Unicode stars.
    E.g., 4 → ⭐⭐⭐⭐
    """
    if rating is None:
        return ""
    full_stars = int(rating)
    return "⭐" * full_stars


def build_poll_embed(book_titles: list[str], deadline: str = None) -> discord.Embed:
    """
    Creates an embed listing candidate books for a poll.
    """
    description = "\n".join(f"{i+1}️⃣ {title}" for i, title in enumerate(book_titles))

    embed = discord.Embed(
        title="📊 Book Club Poll",
        description=description,
        color=discord.Colour.gold(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )

    if deadline:
        embed.set_footer(text=f"Vote by: {deadline}")

    return embed


def build_discussion_thread_embed(book_title: str, author: str, book_url: str, image_url: str = None) -> discord.Embed:
    """
    Embed for a newly created book discussion thread.
    """
    embed = discord.Embed(
        title=book_title,
        url=book_url,
        description="🎉 **This is the official discussion thread!**",
        color=discord.Colour.purple(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    embed.add_field(name="Author", value=author, inline=False)

    if image_url:
        embed.set_thumbnail(url=image_url)

    return embed
