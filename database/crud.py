from database.models import User, Book, UserBook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
load_dotenv()

def create_session():
    conn_str = os.getenv("PG_CONNECTION_STRING")
    engine = create_engine(conn_str, echo=True)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    return db

def create_user(discord_id: int, discord_username: str, goodreads_user_id: str, goodreads_display_name: str) -> User:
    db = create_session()
    db_user = User(discord_id=discord_id, discord_username=discord_username, goodreads_user_id=goodreads_user_id, goodreads_display_name=goodreads_display_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return db_user

def delete_user(discord_id: int) -> None:
    db = create_session()
    db_user = db.query(User).filter(User.discord_id == discord_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    else:
        print(f"User with discord_id {discord_id} not found.")
    db.close()
