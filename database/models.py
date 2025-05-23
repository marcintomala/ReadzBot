from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import Column, Integer, BigInteger, Double, String, Text, ForeignKey, DateTime, PrimaryKeyConstraint, UniqueConstraint, CheckConstraint
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
pg_url = os.getenv("PG_CONNECTION_STRING") if os.getenv("ENV") == "dev" else os.getenv("PG_CONNECTION_STRING").replace("localhost", os.getenv("PG_HOST"))
engine = create_async_engine(pg_url, echo=True)

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class Server(Base):
    __tablename__ = "servers"
    server_id = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    server_name = Column(String, nullable=False)

    users = relationship("User", back_populates="server")
    user_books = relationship("UserBook", back_populates="server")
    settings = relationship("ServerSettings", back_populates="server")
    forum_threads = relationship("ForumThread", back_populates="server")
    progress_updates = relationship("ProgressUpdate", back_populates="server")
    
class ServerSettings(Base):
    __tablename__ = "server_settings"
    server_id = Column(BigInteger, ForeignKey("servers.server_id"), primary_key=True)
    channel_id = Column(BigInteger)
    channel_type = Column(String, nullable=False)
    __table_args__ = (
        CheckConstraint("channel_type IN ('text', 'forum')", name="ck_channel_type"),
    )

    server = relationship("Server", back_populates="settings")
    
class ForumThread(Base):
    __tablename__ = "forum_threads"
    server_id = Column(BigInteger, ForeignKey("servers.server_id"), nullable=False)
    thread_type = Column(String, nullable=False)
    thread_id = Column(BigInteger, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('server_id', 'thread_type'),
    )
    
    server = relationship("Server", back_populates="forum_threads")

class User(Base):
    __tablename__ = "users"
    server_id = Column(BigInteger, ForeignKey("servers.server_id"))
    user_id = Column(BigInteger, unique=True, nullable=False)
    discord_username = Column(String, nullable=False)
    goodreads_user_id = Column(String)
    goodreads_display_name = Column(String)
    registered_at = Column(DateTime, default=datetime.utcnow)

    server = relationship("Server", back_populates="users")
    books = relationship("UserBook", back_populates="user")
    progress_updates = relationship("ProgressUpdate", back_populates="user")
    
    __table_args__ = (
        PrimaryKeyConstraint('server_id', 'user_id'),
    )

class Book(Base):
    __tablename__ = "books"
    book_id = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    cover_image_url = Column(String)
    goodreads_url = Column(String)
    average_rating = Column(Double)

    users = relationship("UserBook", back_populates="book")

class UserBook(Base):
    __tablename__ = "user_books"
    server_id = Column(BigInteger, ForeignKey("servers.server_id"))
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    book_id = Column(BigInteger, ForeignKey("books.book_id"))
    shelf = Column(String)
    rating = Column(Integer)
    review = Column(Text)
    review_date = Column(DateTime)

    server = relationship("Server", back_populates="user_books")
    user = relationship("User", back_populates="books")
    book = relationship("Book", back_populates="users")
    
    __table_args__ = (
        PrimaryKeyConstraint('server_id', 'user_id', 'book_id'),
        UniqueConstraint("server_id", "user_id", "book_id", name="uq_user_book"),
    )
    
class ProgressUpdate(Base):
    __tablename__ = "progress_updates"
    server_id = Column(BigInteger, ForeignKey("servers.server_id"))
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    value = Column(String)
    published = Column(DateTime)

    server = relationship("Server", back_populates="progress_updates")
    user = relationship("User", back_populates="progress_updates")

    __table_args__ = (
        PrimaryKeyConstraint('server_id', 'user_id', 'published'),
        UniqueConstraint("server_id", "user_id", "published", name="uq_progress_update"),
    )

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
