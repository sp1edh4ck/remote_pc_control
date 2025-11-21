from .db_engine import create_pool
from .models import TABLES_SQL


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Создаёт пул подключений к PostgreSQL."""
        if self.pool is not None:
            return
        try:
            self.pool = await create_pool()
        except Exception as e:
            raise RuntimeError(f"Не удалось подключиться к PostgreSQL: {e}")
        # if self.pool is None:
        #     try:
        #         self.pool = await create_pool()
        #     except:
        #         return

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
        if not self.pool:
            raise RuntimeError("drop_all_tables() вызвано до подключения к БД")
        async with self.pool.acquire() as conn:
            tables = await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public';"
            )
            if not tables:
                return
            for t in tables:
                table = t["tablename"]
                try:
                    await conn.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                except Exception as e:
                    raise RuntimeError(f"Ошибка удаления таблицы {table}: {e}")

    async def user_exists(self, client_id):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT 1 FROM users WHERE client_id=$1", client_id)
            return row is not None

    async def add_user(self, client_id):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO users (client_id) VALUES ($1)", client_id)

    async def get_users(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM users")

    async def set_user_client_id(self, old_id, new_id):
        async with self.pool.acquire() as conn:
            result = await conn.execute("UPDATE users SET client_id=$1 WHERE client_id=$2", new_id, old_id)
            try:
                updated = int(result.split()[-1]) > 0
            except Exception:
                updated = False
            return updated