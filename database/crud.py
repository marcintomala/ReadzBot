from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from database.models import Server, User, Book, UserBook, ServerSettings, ForumThread, ProgressUpdate
from discord import Guild
from datetime import datetime
import logging

# -----------------------
# User Functions
# -----------------------
async def create_user(session: AsyncSession, server_id: int, user_id: int, discord_username: str, goodreads_user_id: str, goodreads_display_name: str) -> User:
    db_user = User(server_id=server_id, user_id=user_id, discord_username=discord_username, goodreads_user_id=goodreads_user_id, goodreads_display_name=goodreads_display_name)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def delete_user(session: AsyncSession, user_id: int, server_id: int) -> None:
    result = await session.execute(select(User).where(User.user_id == user_id, User.server_id == server_id))
    db_user = result.scalar_one_or_none()
    if db_user:
        await session.delete(db_user)
        await session.commit()

async def get_user(session: AsyncSession, server_id: int, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.server_id == server_id, User.user_id == user_id))
    return result.scalar_one_or_none()

async def get_all_users(session: AsyncSession, server_id: int) -> list[User]:
    result = await session.execute(select(User).where(User.server_id == server_id))
    return result.scalars().all()

# -----------------------
# Book Functions
# -----------------------
async def save_book(session: AsyncSession, book_id: str, title: str, author: str, cover_image_url: str, goodreads_url: str, average_rating: float) -> Book | None:
    stmt = select(Book).where(Book.book_id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if book:
        return book

    book = Book(
        book_id=book_id,
        title=title,
        author=author,
        cover_image_url=cover_image_url,
        goodreads_url=goodreads_url,
        average_rating=average_rating,
    )
    session.add(book)
    await session.flush()
    return book

async def delete_book(session: AsyncSession, book_id: str) -> None:
    result = await session.execute(select(Book).where(Book.book_id == book_id))
    db_book = result.scalar_one_or_none()
    if db_book:
        await session.delete(db_book)
        await session.commit()
        
async def get_all_books(session: AsyncSession) -> list[Book]:
    result = await session.execute(select(Book))
    return result.scalars().all()

async def get_book_by_title(session: AsyncSession, title: str) -> Book | None:
    result = await session.execute(select(Book).where(Book.title == title))
    return result.scalar_one_or_none()

# -----------------------
# UserBook Functions
# -----------------------
async def save_user_book(session: AsyncSession, server_id: int, user_id: int, book_id: int, shelf: str, rating: int = None, review: str = None, review_date: datetime = None) -> UserBook:
    stmt = (
        insert(UserBook)
        .values(
            server_id=server_id,
            user_id=user_id,
            book_id=book_id,
            shelf=shelf,
            rating=rating,
            review=review,
            review_date=review_date.replace(tzinfo=None) if review_date and review_date.tzinfo else review_date,
        )
        .on_conflict_do_update(
            index_elements=["server_id", "user_id", "book_id"],
            set_={
                "shelf": shelf,
                "rating": rating,
                "review": review,
                "review_date": review_date.replace(tzinfo=None) if review_date and review_date.tzinfo else review_date,
            }
        )
    )
    try:
        await session.execute(stmt)
        await session.commit()
    except Exception as e:
        await session.rollback()
        logging.error(f"Error saving user book: {e}")

async def delete_user_book(session: AsyncSession, server_id: int, user_id: int, book_id: int) -> None:
    result = await session.execute(select(UserBook).where(UserBook.server_id == server_id, UserBook.user_id == user_id, UserBook.book_id == book_id))
    db_user_book = result.scalar_one_or_none()
    if db_user_book:
        await session.delete(db_user_book)
        await session.commit()
        
async def get_all_user_books(session: AsyncSession, server_id: int, user_id: int) -> list[UserBook]:
    result = await session.execute(select(UserBook).options(selectinload(UserBook.book), selectinload(UserBook.user)).where(UserBook.server_id == server_id, UserBook.user_id == user_id))
    return result.scalars().all()

# -----------------------
# Server Functions
# -----------------------
async def save_server(session: AsyncSession, guild: Guild) -> Server:
    db_server = Server(server_id=guild.id, server_name=guild.name)
    session.add(db_server)
    await session.commit()
    await session.refresh(db_server)
    return db_server

async def get_all_servers(session: AsyncSession) -> list[Server]:
    result = await session.execute(select(Server))
    return result.scalars().all()

async def get_server_by_server_id(session: AsyncSession, server_id: int) -> Server | None:
    result = await session.execute(select(Server).where(Server.server_id == server_id))
    return result.scalar_one_or_none()

# -----------------------
# ServerSettings Functions
# -----------------------

# Set channel
async def set_notification_channel(session, server_id: int, channel_id: int, channel_type: str):
    stmt = (
        insert(ServerSettings)
        .values(
            server_id=server_id,
            channel_id=channel_id,
            channel_type=channel_type,
        )
        .on_conflict_do_update(
            index_elements=["server_id"],
            set_={
                "channel_id": channel_id,
                "channel_type": channel_type,
            }
        )
    )
    await session.execute(stmt)
    await session.commit()

# Get channel info
async def get_notification_channel(session, server_id: int) -> ServerSettings | None:
    result = await session.execute(
        select(ServerSettings).where(ServerSettings.server_id == server_id)
    )
    return result.scalar_one_or_none()

# ------------------------
# Forum Threads Functions
# ------------------------

# Set or update a forum thread
async def set_forum_thread(session, server_id: int, thread_type: str, thread_id: int):
    from database.models import ForumThread  # adjust path if needed
    stmt = (
        insert(ForumThread)
        .values(
            server_id=server_id,
            thread_type=thread_type,
            thread_id=thread_id,
        )
        .on_conflict_do_update(
            index_elements=["server_id", "thread_type"],
            set_={"thread_id": thread_id}
        )
    )
    await session.execute(stmt)
    await session.commit()

# Get a specific thread
async def get_forum_thread(session, server_id: int, thread_type: str):
    result = await session.execute(
        select(ForumThread.thread_id).where(
            ForumThread.server_id == server_id,
            ForumThread.thread_type == thread_type
        )
    )
    row = result.first()
    return row[0] if row else None

# Get all threads for a server (optional)
async def get_all_forum_threads(session, server_id: int):
    result = await session.execute(
        select(ForumThread.thread_type, ForumThread.thread_id).where(
            ForumThread.server_id == server_id
        )
    )
    return {row.thread_type: row.thread_id for row in result.fetchall()}


# ------------------------
# Progress Updates Functions
# ------------------------
async def save_new_update(session, server_id: int, user_id: int, update_value: str, published_at: datetime):
    new_update = ProgressUpdate(
        server_id=server_id,
        user_id=user_id,
        value=update_value,
        published=published_at.replace(tzinfo=None) if published_at and published_at.tzinfo else published_at,
    )
    session.add(new_update)
    await session.commit()
    
async def check_sent_update(session, server_id: int, user_id: int, published_at: datetime) -> bool:
    result = await session.execute(
        select(ProgressUpdate).where(
            ProgressUpdate.server_id == server_id,
            ProgressUpdate.user_id == user_id,
            ProgressUpdate.published == published_at.replace(tzinfo=None) if published_at and published_at.tzinfo else published_at
        )
    )
    return result.scalar_one_or_none() is not None