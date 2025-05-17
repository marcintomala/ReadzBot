import feedparser as fp
from database.connection import AsyncSessionLocal
import database.crud as crud
from datetime import datetime
import logging


GOODREADS_BOOK_URL_STUB = 'https://www.goodreads.com/book/show/'

async def read_feed(goodreads_user_id):
    # Fetch the RSS feed from Goodreads and parse it - filtering out custom shelves
    RSS_URL = f'https://www.goodreads.com/review/list_rss/{goodreads_user_id}?shelf=all'
    feed = fp.parse(RSS_URL)
    return [entry for entry in feed.entries if entry.user_shelves in ['read', 'currently-reading', 'to-read']]

async def process_feed_entries(server_id, user_id, entries):
    for entry in entries:
        goodreads_book_id = entry.book_id
        title = entry.title
        author = entry.author_name
        cover_image_url = entry.book_image_url
        goodreads_url = GOODREADS_BOOK_URL_STUB + goodreads_book_id
        publish_time = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
        shelf = entry.user_shelves
        rating = int(entry.user_rating) if entry.user_rating else None
        average_rating = float(entry.average_rating) if entry.average_rating else None
        review = entry.user_review if entry.user_review else None
        
        logging.info(f"Processing entry: {title} by {author} for user: {user_id} on shelf: {shelf}")
    
        async with AsyncSessionLocal() as session:
            book = await crud.save_book(session, server_id, goodreads_book_id, title, author, cover_image_url, goodreads_url, average_rating)
            if book:
                await crud.save_user_book(session, server_id, user_id, book.id, shelf, rating, review, publish_time)
                
    # Check for books that are no longer in the feed
    # and remove them from the user's list
    async with AsyncSessionLocal() as session:
        books = await crud.get_all_books(session, server_id)
        user_books = await crud.get_all_user_books(session, server_id, user_id)
        for user_book in user_books:
            if user_book.book_id not in [book.id for book in books]:
                await crud.delete_user_book(session, server_id, user_book.user_id, user_book.book_id)
        
async def process(server_id = None):
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
            users = await crud.get_all_users(session=session, server_id=server.id)
            if len(users) == 0:
                logging.warning(f"No shelves found for server {server.server_id}.")
                return
            for user in users:
                logging.info(f"Processing user: {user.discord_id} from server: {server.server_id}")
                entries = await read_feed(user.goodreads_user_id)
                await process_feed_entries(server.id, user.id, entries)
                logging.info(f"Processed {len(entries)} entries for user: {user.discord_id} from server: {server.server_id}")
    logging.info(f'Processing feeds for all users for server {server.server_id} completed.')