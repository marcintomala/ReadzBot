import feedparser as fp
from database.connection import AsyncSessionLocal
import database.crud as crud
from database.models import UserBook
from datetime import datetime
from cogs.message_sender import send_update_message
from cogs.FeedEntry import FeedEntry
import logging



def read_feed(goodreads_user_id: str) -> list[FeedEntry]:
    RSS_URL = f'https://www.goodreads.com/review/list_rss/{goodreads_user_id}?shelf=all'
    feed = fp.parse(RSS_URL)
    entries = []

    for entry in feed.entries:
        raw_shelf = entry.get("user_shelves", "").strip().lower()
        raw_review = entry.get("user_review", "").strip()
        
        if raw_shelf in ['read', 'currently-reading', 'to-read']:
            resolved_shelf = raw_shelf
        elif raw_review:
            resolved_shelf = "read"
        else:
            continue
        
        try:
            feed_entry = FeedEntry(
                book_id=int(entry.book_id),
                title=entry.title,
                author=entry.get("author_name"),
                cover_image_url=entry.get("book_image_url"),
                goodreads_url=f"https://www.goodreads.com/book/show/{entry.book_id}",
                shelf=resolved_shelf,
                rating=int(entry.user_rating) if entry.user_rating else None,
                average_rating=float(entry.average_rating) if entry.average_rating else None,
                review=raw_review if raw_review else None,
                published=datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
            )
            entries.append(feed_entry)
        except Exception as e:
            print(f"⚠️ Skipping entry due to parse error: {e}")
    return entries

async def cleanup(server_id, user_id, user_books: list[UserBook], feed_entries: list[FeedEntry]):
    # Check for books that are no longer in the feed
    # and remove them from the user's list
    current_feed_book_ids = {entry.book_id for entry in feed_entries}

    async with AsyncSessionLocal() as session:
        for user_book in user_books:
            if user_book.book_id not in current_feed_book_ids:
                await crud.delete_user_book(session, server_id, user_id, user_book.book_id)
    return user_books
                
async def resolve_feed_updates(user_books: list[UserBook], feed_entries: list[FeedEntry]):
    # Check for books not in the database but in the feed to produce a update message for Discord
    db_book_ids = {user_book.book_id for user_book in user_books}
    new_books = [entry for entry in feed_entries if int(entry.book_id) not in db_book_ids]
    return new_books
        
async def save_entries(server_id, user_id, feed_entries: list[FeedEntry]):
    async with AsyncSessionLocal() as session:
        for entry in feed_entries:
            logging.info(f"Processing entry: {entry.title} by {entry.author} for user: {user_id} on shelf: {entry.shelf}")
        
            await crud.save_book(session, server_id, entry.book_id, entry.title, entry.author, entry.cover_image_url, entry.goodreads_url, entry.average_rating)
            await crud.save_user_book(session, server_id, user_id, entry.book_id, entry.shelf, entry.rating, entry.review, entry.published)
    
async def process_feed(server_id, user_id, feed_entries: list[FeedEntry]):
    # First get all the books for the user
    async with AsyncSessionLocal() as session:
        user_books = await crud.get_all_user_books(session, server_id, user_id)
    
    # Then clean up the database by removing books that are no longer in the feed
    await cleanup(server_id, user_id, user_books, feed_entries)
    
    # Then save the feed entries
    await save_entries(server_id, user_id, feed_entries)
    
    # Then resolve and return feed updates
    return await resolve_feed_updates(user_books, feed_entries)
                
async def process(bot, server_id = None):
    logging.info("Processing feeds started...")
    async with AsyncSessionLocal() as session:
        if server_id:
            server = await crud.get_server_by_server_id(session=session, server_id=server_id)
            if not server:
                logging.error(f"Server {server_id} not found in the database.")
                return
            servers = [server]
        else:
            servers = await crud.get_all_servers(session=session)
            if len(servers) == 0:
                logging.warning("No servers found in the database.")
                return
        for server in servers:
            logging.info(f"Processing feeds for server {server.server_name} ({server.server_id})")
            users = await crud.get_all_users(session=session, server_id=server.server_id)
            update_thread_id = await crud.get_forum_thread(session, server_id, "update")
            if len(users) == 0:
                logging.warning(f"No shelves found for server {server.server_id}.")
                return
            for user in users:
                logging.info(f"Processing user: {user.user_id} from server: {server.server_id}")
                feed_entries = read_feed(user.goodreads_user_id)
                updates = await process_feed(server.server_id, user.user_id, feed_entries)
                logging.info(f"Processed {len(feed_entries)} entries for user: {user.user_id} from server: {server.server_id}")
                # Send updates to Discord
                if update_thread_id and len(updates) > 0:
                    await send_update_message(bot, update_thread_id, user.user_id, updates)
                else:
                    logging.warning(f"No update thread found for server {server.server_id}. Cannot send updates.")
    logging.info(f'Processing feeds for all users for server {server.server_id} completed. Sending updates to Discord...')
    