from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Server, User, Book, UserBook
from discord import Guild
from datetime import datetime

# -----------------------
# User Functions
# -----------------------
async def create_user(session: AsyncSession, server_id: int, discord_id: int, discord_username: str, goodreads_user_id: str, goodreads_display_name: str) -> User:
    db_user = User(server_id=server_id, discord_id=discord_id, discord_username=discord_username, goodreads_user_id=goodreads_user_id, goodreads_display_name=goodreads_display_name)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def delete_user(session: AsyncSession, discord_id: int, server_id: int) -> None:
    result = await session.execute(select(User).where(User.discord_id == discord_id, User.server_id == server_id))
    db_user = result.scalar_one_or_none()
    if db_user:
        await session.delete(db_user)
        await session.commit()

async def get_user(session: AsyncSession, server_id: int, discord_id: int) -> User | None:
    result = await session.execute(select(User).where(User.server_id == server_id, User.discord_id == discord_id))
    return result.scalar_one_or_none()

async def get_all_users(session: AsyncSession, server_id: int) -> list[User]:
    result = await session.execute(select(User).where(User.server_id == server_id))
    return result.scalars().all()

# -----------------------
# Book Functions
# -----------------------
async def save_book(session: AsyncSession, server_id: int, goodreads_book_id: str, title: str, author: str, cover_image_url: str, goodreads_url: str, average_rating: float) -> Book | None:
    result = await session.execute(select(Book).where(Book.goodreads_book_id == goodreads_book_id))
    if result.scalar_one_or_none():
        return None
    db_book = Book(server_id=server_id, goodreads_book_id=goodreads_book_id, title=title, author=author, cover_image_url=cover_image_url, goodreads_url=goodreads_url, average_rating=average_rating)
    session.add(db_book)
    await session.commit()
    await session.refresh(db_book)
    return db_book

async def delete_book(session: AsyncSession, server_id: int, goodreads_book_id: str) -> None:
    result = await session.execute(select(Book).where(Book.server_id == server_id, Book.goodreads_book_id == goodreads_book_id))
    db_book = result.scalar_one_or_none()
    if db_book:
        await session.delete(db_book)
        await session.commit()
        
async def get_all_books(session: AsyncSession, server_id: int) -> list[Book]:
    result = await session.execute(select(Book).where(Book.server_id == server_id))
    return result.scalars().all()

# -----------------------
# UserBook Functions
# -----------------------
async def save_user_book(session: AsyncSession, server_id: int, user_id: int, book_id: int, shelf: str, rating: int = None, review: str = None, review_date: datetime = None) -> UserBook:
    db_user_book = UserBook(server_id=server_id, user_id=user_id, book_id=book_id, shelf=shelf, rating=rating, review=review, review_date=review_date.replace(tzinfo=None) if review_date and review_date.tzinfo else review_date
)
    merged_user_book = await session.merge(db_user_book)
    await session.commit()
    await session.refresh(merged_user_book)
    return merged_user_book

async def delete_user_book(session: AsyncSession, server_id: int, user_id: int, book_id: int) -> None:
    result = await session.execute(select(UserBook).where(UserBook.server_id == server_id, UserBook.user_id == user_id, UserBook.book_id == book_id))
    db_user_book = result.scalar_one_or_none()
    if db_user_book:
        await session.delete(db_user_book)
        await session.commit()
        
async def get_all_user_books(session: AsyncSession, server_id: int, user_id: int) -> list[UserBook]:
    result = await session.execute(select(UserBook).where(UserBook.server_id == server_id, UserBook.user_id == user_id))
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
