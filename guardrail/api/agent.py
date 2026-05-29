# guardrail/api/agent.py
# WebSocket API routing for human agent live dashboard streams

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from guardrail.escalation.queue import agent_manager

router = APIRouter()


@router.websocket("/api/v1/agent/dashboard")
async def handle_agent_dashboard(websocket: WebSocket):
    """Register agent WebSocket connection to receive live escalation broadcasts."""
    await agent_manager.connect(websocket)
    try:
        while True:
            # Keep socket alive; ignore incoming agent packets
            await websocket.receive_text()
    except WebSocketDisconnect:
        agent_manager.disconnect(websocket)
    except Exception:
        agent_manager.disconnect(websocket)
        await websocket.close()
