import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from bot.handlers import callbacks, commands
from bot.service.loader import bot, db, dp, logger
from routes.files import router as files_router
from routes.websocket import router as ws_router


async def start_bot_safe():
    """Безопасный запуск Telegram-бота с автоперезапуском."""
    while True:
        try:
            logger.info("Запуск Telegram бота...")
            await dp.start_polling(bot)
        except asyncio.CancelledError:
            logger.info("Telegram бот остановлен.")
            break
        except Exception as e:
            logger.error(f"❗ Ошибка в боте: {e}. Перезапуск через 5 секунд...")
            await asyncio.sleep(5)


async def connect_db_safe():
    """Безопасное подключение к БД с повторными попытками."""
    for attempt in range(5):
        try:
            await db.connect()
            await db.create_tables()
            logger.info("База данных готова.")
            return
        except Exception as e:
            logger.error(f"Ошибка подключения к БД ({attempt+1}/5): {e}")
            await asyncio.sleep(3)
    logger.critical("Не удалось подключиться к БД. Сервер запущен БЕЗ базы.")


@asynccontextmanager
async def lifespan(app):
    """Современное управление жизненным циклом FastAPI."""
    bot_task = asyncio.create_task(start_bot_safe())
    try:
        dp.include_router(callbacks.router)
        dp.include_router(commands.router)
    except Exception as e:
        logger.error(f"Ошибка подключения Telegram-роутеров: {e}")
    await connect_db_safe()
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

try:
    app.include_router(ws_router)
except Exception as e:
    logger.critical(f"Ошибка инициализации websocket router: {e}")

try:
    app.include_router(files_router)
except Exception as e:
    logger.critical(f"Ошибка инициализации files router: {e}")

if __name__ == "__main__":
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=1337,
            log_level="critical"
        )
    except Exception as e:
        logger.critical(f"Uvicorn критическая ошибка: {e}")
