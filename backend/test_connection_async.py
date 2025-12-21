import os
import asyncio
import re
from sqlalchemy import text
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

async def async_main() -> None:
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL not found in .env file")
        return
    
    # Convert postgresql:// to postgresql+asyncpg:// for async support
    # Remove sslmode and channel_binding params (asyncpg handles SSL differently)
    async_url = re.sub(r'^postgresql:', 'postgresql+asyncpg:', database_url)
    # Remove sslmode and channel_binding parameters
    async_url = re.sub(r'[?&]sslmode=[^&]*', '', async_url)
    async_url = re.sub(r'[?&]channel_binding=[^&]*', '', async_url)
    # Clean up any double ? or trailing &
    async_url = re.sub(r'\?&', '?', async_url)
    async_url = re.sub(r'&+', '&', async_url)
    async_url = async_url.rstrip('&?')
    
    engine = create_async_engine(async_url, echo=True, connect_args={"ssl": "require"})
    async with engine.connect() as conn:
        result = await conn.execute(text("select 'hello world'"))
        print(result.fetchall())
    await engine.dispose()

asyncio.run(async_main())

