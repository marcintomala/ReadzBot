import discord
from discord.ext import commands
import datetime as dt
from database.models import User
from collections import defaultdict
from cogs.FeedEntry import FeedEntry
import re

GOODREADS_BOOK_URL_STUB = 'https://www.goodreads.com/book/show/'
GOODREADS_USER_URL_STUB = 'https://www.goodreads.com/user/show/'
MASS_UPDATE_THRESHOLD = 2

async def send_update_message(bot: commands.Bot, thread_id: int, user: User, entries: list[FeedEntry]):
    """
    Sends a feed update message to the appropriate 'update' thread for a given server.
    Requires the bot instance, server ID, and a parsed feed entry.
    """
    
    thread = bot.get_channel(thread_id)
    emojis = thread.guild.emojis
        
    discord_user = await bot.fetch_user(user.user_id)

    if thread is None:
        print(f"⚠️ Thread ID {thread_id} not found in bot cache.")
        return
    
    to_read = [entry for entry in entries if entry.shelf == "to-read"]
    rest = [entry for entry in entries if entry.shelf != "to-read"]
    
    if len(rest) > MASS_UPDATE_THRESHOLD:
        embed = build_batch_feed_update_embed(entries, emojis, user, discord_user)
        await thread.send(embed=embed)
        return
    elif len(to_read) > 0:
        to_read_embed = build_batch_feed_update_embed(to_read, emojis, user, discord_user)
        await thread.send(embed=to_read_embed)
    
    for entry in rest:
        if entry is None:
            continue
        if entry.shelf == "read":
            embed = build_finished_book_embed(entry, emojis, user, discord_user)
            await thread.send(embed=embed)
        elif entry.shelf == "currently-reading":
            embed = build_current_book_embed(entry, emojis, user, discord_user)
            await thread.send(embed=embed)

def build_batch_feed_update_embed(entries: list[FeedEntry], emojis: tuple, user: User, discord_user: discord.User) -> discord.Embed:
    """
    Build a single embed for multiple book updates.
    `entries` is a list of dicts with keys like:
        - title, author, link, user_shelves, rating
    """

    embed = discord.Embed(
        title=f'{discord.utils.get(emojis, name="applecat")} Goodreads Update',
        description=f'{discord.utils.get(emojis, name="RonaldoPog")} {discord_user.mention} ([{user.goodreads_display_name}]({GOODREADS_USER_URL_STUB}{user.goodreads_user_id})) updated their shelves!',
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

        MAX_FIELD_LEN = 1024

        def chunk_lines(lines: list[str], max_len: int = MAX_FIELD_LEN) -> list[str]:
            chunks = []
            current = []
            current_len = 0
            for line in lines:
                line_len = len(line) + 1  # +1 for newline
                if current_len + line_len > max_len:
                    chunks.append("\n".join(current))
                    current = [line]
                    current_len = line_len
                else:
                    current.append(line)
                    current_len += line_len
            if current:
                chunks.append("\n".join(current))
            return chunks

        chunks = chunk_lines(lines)
        for i, chunk in enumerate(chunks):
            suffix = f" ({i+1}/{len(chunks)})" if len(chunks) > 1 else ""
            embed.add_field(name=pretty_shelf + suffix, value=chunk, inline=False)
    embed.set_author(name=user.discord_username, icon_url=discord_user.avatar)

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

def build_finished_book_embed(book: FeedEntry, emojis: tuple, user: User, discord_user: discord.User) -> discord.Embed:
    """
    Embed for a finished book, with extra flair!
    """
    duck_ass = discord.utils.get(emojis, name="duckAss")
    nyanod = discord.utils.get(emojis, name="nyanod") or "📚"
    applecat = discord.utils.get(emojis, name="applecat")
    user_line = f"[{user.goodreads_display_name}]({GOODREADS_USER_URL_STUB}{user.goodreads_user_id})"
    finished_line = f"{duck_ass} {user_line} just **finished reading**:"
    review_section = f"\n\n> {book.review}" if book.review else ""
    description = (
        f"{finished_line}\n"
        f"**[{book.title}]({GOODREADS_BOOK_URL_STUB}{book.book_id})** by *{book.author}* {nyanod}\n"
        f"{review_section}"
    )

    embed = discord.Embed(
        title=f'{applecat} Goodreads Update',
        description=description,
        color=discord.Colour.green(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    embed.set_author(name=user.discord_username, icon_url=discord_user.avatar)
    embed.set_thumbnail(url=book.cover_image_url)

    if book.rating > 0:
        stars = render_stars(book.rating)
        embed.add_field(name="Rating", value=stars, inline=True)

    return embed

def build_current_book_embed(book: FeedEntry, emojis: tuple, user: User, discord_user: discord.User) -> discord.Embed:
    """
    Embed for a currently reading book, with extra flair!
    """
    blurryeyes = discord.utils.get(emojis, name="blurryeyes") or "📖"
    applecat = discord.utils.get(emojis, name="applecat")
    sparkle = "✨"
    now_reading = f"{sparkle} **Now Reading!** {sparkle}"
    user_line = f"[{user.goodreads_display_name}]({GOODREADS_USER_URL_STUB}{user.goodreads_user_id})"
    description = (
        f"{now_reading}\n\n"
        f"{discord_user.mention} ({user_line}) just started:\n"
        f"**[{book.title}]({GOODREADS_BOOK_URL_STUB}{book.book_id})** by *{book.author}* {blurryeyes}"
    )

    embed = discord.Embed(
        title=f'{applecat} Goodreads Update',
        description=description,
        color=discord.Colour.purple(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    embed.set_author(name=user.discord_username, icon_url=discord_user.avatar)
    embed.set_thumbnail(url=book.cover_image_url)

    return embed

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

async def send_progress_update_message(bot: commands.Bot, thread_id: int, user: User, update: dict):
    """
    Sends a reading progress update message to the appropriate 'update' thread for a given server.
    Requires the bot instance, server ID, and a parsed feed entry.
    """
    
    thread = bot.get_channel(thread_id)
    emojis = thread.guild.emojis
        
    discord_user = await bot.fetch_user(user.user_id)

    if thread is None:
        print(f"⚠️ Thread ID {thread_id} not found in bot cache.")
        return
    
    if update['message_id']:
        last_update_message = await thread.fetch_message(update['message_id'])
        if last_update_message:
            await last_update_message.delete()
    embed = build_progress_update_embed(update, user, discord_user, emojis)
    return await thread.send(embed=embed)

def build_progress_update_embed(update, user: User, discord_user: discord.User, emojis: tuple = ()) -> discord.Embed:
    """
    Build an embed for a Goodreads reading progress update.
    Supports both percentage and page-based updates.
    """

    # Try to extract progress info from entry.title
    title = update['value']
    book_title = None
    progress_text = None

    # Patterns for percentage and page-based updates
    percent_pattern = re.compile(r"(.+?) is (\d+)% done with (.+)")
    page_pattern = re.compile(r"(.+?) is on page (\d+) of (\d+) of (.+)")
    
        # Optionally, get a book cover if available
    book = update['book'] if update['book'] else None
    cover_url = book.cover_image_url if book else None
    
    # Optionally, add a link to the book if available
    book_url = book.goodreads_url if book else None

    if percent_match := percent_pattern.match(title):
        user_name, percent, book_title = percent_match.groups()
        progress_text = f"**{user.goodreads_display_name}** is **{percent}%** done with **[{book.title}]({book_url})**!"
        progress_emoji = "📈"
    elif page_match := page_pattern.match(title):
        user_name, page, total, book_title = page_match.groups()
        progress_text = f"**{user.goodreads_display_name}** is on page **{page}** of **{total}** of **[{book.title}]({book_url})**!"
        progress_emoji = "📖"
    else:
        # Fallback: just show the title
        progress_text = title
        progress_emoji = "📚"

    embed = discord.Embed(
        title=f"{progress_emoji} Reading Progress Update",
        description=progress_text,
        color=discord.Colour.purple(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    embed.set_author(name=user.discord_username, icon_url=discord_user.avatar)
    if cover_url:
        embed.set_thumbnail(url=cover_url)


    return embed
