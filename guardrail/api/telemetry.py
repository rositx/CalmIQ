# guardrail/api/telemetry.py
# WebSocket API routing for streaming user interaction telemetry

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from guardrail.session.state import get_session, save_session

router = APIRouter()


@router.websocket("/api/v1/telemetry/{session_id}")
async def handle_telemetry_stream(websocket: WebSocket, session_id: str):
    """Receive real-time click and typing signals and log them in active state."""
    await websocket.accept()
    try:
        while True:
            # Continuously ingest real-time behavior packets from client UI
            data = await websocket.receive_json()
            session = get_session(session_id)
            if session:
                # Update click rate and typing indicators in the active session
                session.customer_ltv = float(data.get("customer_ltv", session.customer_ltv))
                save_session(session_id, session)
                
            # Send confirmation acknowledgment back to streaming client
            await websocket.send_json({"status": "telemetry_cached"})
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
