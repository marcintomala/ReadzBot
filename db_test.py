# db_test.py
import asyncio
import asyncpg
import os

async def test_connection():
    try:
        raw_url = os.getenv("DATABASE_URL")
        dsn = raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        conn = await asyncpg.connect(dsn)
        print("✅ Connection successful!")
        await conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())