import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from bot.service.loader import logger
from utils.config_loader import (BUILD_CLIENT_FILE, CLIENT_PATH, LOADER_PATH,
                                 LOADER_VERSION, SIGN_PRIV_PATH)
from utils.tools import compute_file_hash, sign_hash_with_rsa

router = APIRouter()


@router.get("/client_info")
async def client_info():
    try:
        if not os.path.exists(CLIENT_PATH):
            raise HTTPException(status_code=404, detail=f'{BUILD_CLIENT_FILE} not found')
        file_hash = compute_file_hash(CLIENT_PATH)
        if not isinstance(file_hash, str):
            raise ValueError('Хэш файла не удалось вычислить корректно')
        file_size = os.path.getsize(CLIENT_PATH)
        signature = sign_hash_with_rsa(SIGN_PRIV_PATH, file_hash.encode())
        return {
            "filename": BUILD_CLIENT_FILE,
            "hash": file_hash,
            "size": file_size,
            "signature": signature
        }
    except Exception as e:
        logger.error(f'Ошибка /client_info: {e}')
        return JSONResponse({"error": f'Unexpected error: {str(e)}'}, status_code=500)


@router.get("/download_client")
async def download_client():
    try:
        if not os.path.exists(CLIENT_PATH):
            raise HTTPException(status_code=404, detail=f"{BUILD_CLIENT_FILE} not found")
        return FileResponse(CLIENT_PATH, filename=BUILD_CLIENT_FILE)
    except Exception as e:
        logger.error(f'Ошибка /download_client: {e}')
        return JSONResponse({"error": f'Unexpected error: {str(e)}'}, status_code=500)


@router.get("/loader_info")
def loader_info():
    try:
        if not os.path.exists(LOADER_PATH):
            raise HTTPException(status_code=404, detail='loader not found')
        file_hash = compute_file_hash(LOADER_PATH)
        if not isinstance(file_hash, str):
            raise ValueError('Хэш loader не удалось вычислить')
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
    except Exception as e:
        logger.error(f'Ошибка /loader_info: {e}')
        return JSONResponse({"error": f'Unexpected error: {str(e)}'}, status_code=500)


@router.get("/loader_download")
def loader_download():
    try:
        if not os.path.exists(LOADER_PATH):
            raise HTTPException(status_code=404, detail='loader not found')
        return FileResponse(LOADER_PATH, filename=os.path.basename(LOADER_PATH))
    except Exception as e:
        logger.error(f'Ошибка /loader_download: {e}')
        return JSONResponse({"error": f'Unexpected error: {str(e)}'}, status_code=500)
