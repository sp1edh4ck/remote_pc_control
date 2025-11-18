import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from bot.handlers import callbacks, commands
from bot.service.loader import bot, db, dp, logger
from routes.websocket import router as ws_router
from utils.config_loader import (BUILD_CLIENT_FILE, CLIENT_PATH, LOADER_PATH,
                                 LOADER_VERSION, SIGN_PRIV_PATH)
from utils.tools import compute_file_hash, sign_hash_with_rsa


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
            return {"error": f"{BUILD_CLIENT_FILE} not found"}
        file_hash = compute_file_hash(CLIENT_PATH)
        file_size = os.path.getsize(CLIENT_PATH)
        signature = sign_hash_with_rsa(SIGN_PRIV_PATH, file_hash.encode())
        return {
            "filename": BUILD_CLIENT_FILE,
            "hash": file_hash,
            "size": file_size,
            "signature": signature
        }
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@app.get("/download_client")
async def download_client():
    try:
        if not os.path.exists(CLIENT_PATH):
            return {"error": f"{BUILD_CLIENT_FILE} not found"}
        return FileResponse(CLIENT_PATH, filename=BUILD_CLIENT_FILE)
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@app.get("/loader_info")
def loader_info():
    if not os.path.exists(LOADER_PATH):
        return JSONResponse({"error": "loader not found"}, status_code=404)
    file_hash = compute_file_hash(LOADER_PATH)
    size = os.path.getsize(LOADER_PATH)
    with open(SIGN_PRIV_PATH, "rb") as f:
        priv_key_data = f.read()
    signature = sign_hash_with_rsa(priv_key_data, file_hash.encode())
    return {
        "filename": os.path.basename(LOADER_PATH),
        "size": size,
        "hash": file_hash,
        "signature": signature,
        "version": LOADER_VERSION
    }


@app.get("/loader_download")
def loader_download():
    if not os.path.exists(LOADER_PATH):
        return JSONResponse({"error": "loader not found"}, status_code=404)
    return FileResponse(LOADER_PATH, filename=os.path.basename(LOADER_PATH))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=1337,
        log_level="critical"
    )
