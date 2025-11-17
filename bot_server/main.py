import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse

from bot.handlers import callbacks, commands
from bot.service.loader import bot, db, dp, logger
from routes.websocket import router as ws_router
from utils.config_loader import BUILD_FILE, CLIENT_PATH
from utils.tools import compute_file_hash


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

@app.get("/client_info")
async def client_info():
    try:
        if not os.path.exists(CLIENT_PATH):
            return {"error": f"{BUILD_FILE} not found"}
        file_hash = compute_file_hash(CLIENT_PATH)
        file_size = os.path.getsize(CLIENT_PATH)
        return {
            "filename": BUILD_FILE,
            "hash": file_hash,
            "size": file_size
        }
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@app.get("/download_client")
async def download_client():
    try:
        if not os.path.exists(CLIENT_PATH):
            return {"error": f"{BUILD_FILE} not found"}
        return FileResponse(CLIENT_PATH, filename=BUILD_FILE)
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
