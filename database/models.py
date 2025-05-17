from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import Column, Integer, BigInteger, Double, String, Text, ForeignKey, DateTime
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
pg_url = os.getenv("PG_CONNECTION_STRING")
engine = create_async_engine(pg_url, echo=True)

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class Server(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True)
    server_id = Column(BigInteger, unique=True, nullable=False)
    server_name = Column(String, nullable=False)

    users = relationship("User", back_populates="server")
    books = relationship("Book", back_populates="server")
    user_books = relationship("UserBook", back_populates="server")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    discord_id = Column(BigInteger, unique=True, nullable=False)
    discord_username = Column(String, nullable=False)
    goodreads_user_id = Column(String)
    goodreads_display_name = Column(String)
    registered_at = Column(DateTime, default=datetime.utcnow)

    server = relationship("Server", back_populates="users")
    books = relationship("UserBook", back_populates="user")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    goodreads_book_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    cover_image_url = Column(String)
    goodreads_url = Column(String)
    average_rating = Column(Double)

    server = relationship("Server", back_populates="books")
    users = relationship("UserBook", back_populates="book")

class UserBook(Base):
    __tablename__ = "user_books"
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    shelf = Column(String)
    rating = Column(Integer)
    review = Column(Text)
    review_date = Column(DateTime)

    server = relationship("Server", back_populates="user_books")
    user = relationship("User", back_populates="books")
    book = relationship("Book", back_populates="users")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
