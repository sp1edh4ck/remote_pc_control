from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
connected_clients = {}


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket подключение от любого клиента.
    Любой client_id разрешён.
    """
    await websocket.accept()
    connected_clients[client_id] = {"websocket": websocket}
    print(f"[+] Клиент {client_id} подключился")
    try:
        while True:
            msg = await websocket.receive_text()
            print(f"[{client_id}] {msg}")
            await websocket.send_text(f'{msg}')
    except WebSocketDisconnect:
        print(f"[-] Клиент {client_id} отключился")
        connected_clients.pop(client_id, None)
