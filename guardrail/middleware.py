# guardrail/middleware.py
# Public entry point for CalmIQ: IrritationMiddleware class

from typing import Optional, Dict
from guardrail.router import process_user_message


class IrritationMiddleware:
    """Public gateway class for CalmIQ AI Guardrail Middleware."""

    def __init__(self, app=None):
        self.app = app

    async def __call__(self, scope, receive, send):
        """Standard ASGI middleware execution signature."""
        if self.app is not None:
            await self.app(scope, receive, send)

    async def intercept_message(
        self,
        session_id: str,
        customer_id: str,
        text: str,
        telemetry_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> dict:
        """Programmatic interception entry point for chat message processing."""
        return await process_user_message(
            session_id=session_id,
            customer_id=customer_id,
            text=text,
            telemetry_data=telemetry_data,
            metadata=metadata,
        )
