import asyncpg

from app.bot.service import config


async def create_pool():
    """Создаёт пул подключений к PostgreSQL."""
    return await asyncpg.create_pool(
        user=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        host='127.0.0.1',
        port='5432',
        min_size=1,
        max_size=5
    )
