# guardrail/escalation/queue.py
# Real-time WebSocket connection manager for human agent dashboards

from typing import List


class AgentConnectionManager:
    """Manages active human agent dashboard WebSocket streams."""

    def __init__(self):
        self.active_connections: List = []

    async def connect(self, websocket) -> None:
        """Register a new human agent's active WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket) -> None:
        """Unregister a disconnected human agent's WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_escalation(self, payload: dict) -> None:
        """Broadcast an escalation event payload to all active agent dashboards."""
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                # Silently catch anomalies for disconnected channels
                pass


# Global singleton instance for the application lifecycle
agent_manager = AgentConnectionManager()
