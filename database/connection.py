# database/connection.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("PG_CONNECTION_STRING") if os.getenv("ENV") == "dev" else os.getenv("PG_CONNECTION_STRING").replace("localhost", os.getenv("PG_HOST"))

print(f"Connecting to database at {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
