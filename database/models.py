from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import Column, Integer, BigInteger, String, Text, ForeignKey, DateTime, create_engine
from datetime import datetime
from dotenv import load_dotenv
import os


load_dotenv()
pg_url = os.getenv("PG_CONNECTION_STRING")
engine = create_engine(pg_url, echo=True)

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger, unique=True, nullable=False)
    discord_username = Column(String, nullable=False)
    goodreads_user_id = Column(String)
    goodreads_display_name = Column(String)
    registered_at = Column(DateTime, default=datetime.utcnow)

    books = relationship("UserBook", back_populates="user")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    goodreads_book_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    cover_image_url = Column(String)
    goodreads_url = Column(String)

    users = relationship("UserBook", back_populates="book")

class UserBook(Base):
    __tablename__ = "user_books"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    shelf = Column(String)
    rating = Column(Integer)
    review = Column(Text)
    review_date = Column(DateTime)

    user = relationship("User", back_populates="books")
    book = relationship("Book", back_populates="users")

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)