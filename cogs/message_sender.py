from discord import Embed, Colour
from datetime import datetime
from collections import defaultdict

GOODREADS_BOOK_URL_STUB = 'https://www.goodreads.com/book/show/'

async def send_update_message(bot, thread_id: int, discord_username: str, entries: list[dict]):
    """
    Sends a feed update message to the appropriate 'update' thread for a given server.
    Requires the bot instance, server ID, and a parsed feed entry.
    """

    thread = bot.get_channel(thread_id)

    if thread is None:
        print(f"⚠️ Thread ID {thread_id} not found in bot cache.")
        return

    embed = build_batch_feed_update_embed(entries, discord_username)
    await thread.send(embed=embed)

def build_batch_feed_update_embed(entries: list[dict], user_name: str) -> Embed:
    """
    Build a single embed for multiple book updates.
    `entries` is a list of dicts with keys like:
        - title, author, link, user_shelves, rating
    """

    embed = Embed(
        title=f"@{user_name}'s Reading Update",
        description="Here are the latest Goodreads updates:",
        color=Colour.blue(),
        timestamp=datetime.utcnow()
    )

    # Group by shelf
    grouped = defaultdict(list)
    for e in entries:
        grouped[e["user_shelves"]].append(e)

    for shelf, books in grouped.items():
        lines = []
        for b in books:
            line = f"• [{b['title']}]({GOODREADS_BOOK_URL_STUB + b['book_id']}) by {b['author_name']}"
            if int(b.get("user_rating")) > 0 and shelf == "read":
                stars = render_stars(int(b.get("user_rating")))
                line += f" – {stars}"
            lines.append(line)

        pretty_shelf = {
            "currently-reading": "📘 Currently Reading",
            "read": "✅ Read",
            "to-read": "📚 To Read"
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


def build_poll_embed(book_titles: list[str], deadline: str = None) -> Embed:
    """
    Creates an embed listing candidate books for a poll.
    """
    description = "\n".join(f"{i+1}️⃣ {title}" for i, title in enumerate(book_titles))

    embed = Embed(
        title="📊 Book Club Poll",
        description=description,
        color=Colour.gold(),
        timestamp=datetime.utcnow()
    )

    if deadline:
        embed.set_footer(text=f"Vote by: {deadline}")

    return embed


def build_discussion_thread_embed(book_title: str, author: str, book_url: str, image_url: str = None) -> Embed:
    """
    Embed for a newly created book discussion thread.
    """
    embed = Embed(
        title=book_title,
        url=book_url,
        description="🎉 **This is the official discussion thread!**",
        color=Colour.purple(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Author", value=author, inline=False)

    if image_url:
        embed.set_thumbnail(url=image_url)

    return embed
