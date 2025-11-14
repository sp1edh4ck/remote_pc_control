import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bot.handlers import callbacks, commands
from app.bot.service.loader import bot, db, dp, logger
from app.routes.websocket import router as ws_router


@asynccontextmanager
async def lifespan(app):
    """Современное управление жизненным циклом FastAPI."""
    bot_task = asyncio.create_task(dp.start_polling(bot))
    dp.include_router(callbacks.router)
    dp.include_router(commands.router)
    await db.connect()
    # await db.clear_all_tables()
    # await db.drop_all_tables()
    await db.create_tables()
    logger.info("Telegram бот запущен.")
    yield
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        logger.info("Telegram бот остановлен.")

app = FastAPI(
    title="Remote PC Control Server",
    lifespan=lifespan,
)

app.include_router(ws_router)
