import asyncio
from contextlib import asynccontextmanager
import uvicorn
from app.bot.handlers import callbacks, commands
from app.bot.service.loader import bot, dp
from app.routes.websocket import router as ws_router
from fastapi import FastAPI
from app.bot.utils.logger import setup_logger

logger = setup_logger()


@asynccontextmanager
async def lifespan(app):
    """Современное управление жизненным циклом FastAPI."""
    bot_task = asyncio.create_task(dp.start_polling(bot))
    dp.include_router(callbacks.router)
    dp.include_router(commands.router)
    logger.info("✅ Telegram бот запущен")
    yield
    bot_task.close()
    try:
        await bot_task
    except asyncio.CancelledError:
        logger.info("🛑 Telegram бот остановлен")

app = FastAPI(
    title="Remote PC Control Server",
    lifespan=lifespan,
)

app.include_router(ws_router)
