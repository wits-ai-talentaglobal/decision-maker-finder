from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/ws/jobs")
async def jobs_websocket(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            # Client doesn't need to send anything; this just keeps the connection open
            # and lets us detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
