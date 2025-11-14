from .db_engine import create_pool
from .models import TABLES_SQL


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Создаёт пул подключений к PostgreSQL."""
        if self.pool is None:
            try:
                self.pool = await create_pool()
            except:
                return

    async def create_tables(self):
        """Создаёт все таблицы из models.TABLES_SQL."""
        async with self.pool.acquire() as conn:
            for query in TABLES_SQL:
                await conn.execute(query)

    async def clear_all_tables(self):
        """Очищает все таблицы в бд."""
        async with self.pool.acquire() as conn:
            tables = await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            )
            for t in tables:
                await conn.execute(
                    f'TRUNCATE TABLE "{t["tablename"]}" RESTART IDENTITY CASCADE'
                )

    async def drop_all_tables(self):
        """Полностью удаляет все таблицы в схеме public."""
        async with self.pool.acquire() as conn:
            tables = await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public';"
            )
            for t in tables:
                table = t["tablename"]
                await conn.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')

    async def user_exists(self, uuid):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT 1 FROM users WHERE uuid=$1", uuid)
            return row is not None

    async def add_user(self, uuid):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO users (uuid) VALUES ($1)", uuid)

    async def get_users(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM users")
