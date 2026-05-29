# guardrail/api/chat.py
# REST API routing for client message intercepts

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
from guardrail.middleware import IrritationMiddleware

router = APIRouter()
middleware = IrritationMiddleware()


class MessageRequest(BaseModel):
    """Pydantic schema representing client POST request body."""

    session_id: str
    customer_id: str
    message: str
    telemetry_data: Optional[Dict] = Field(default=None)
    metadata: Optional[Dict] = Field(default=None)


@router.post("/api/v1/chat/message")
async def handle_message(payload: MessageRequest):
    """Intercept client chat message, evaluate irritation, and forward or sever."""
    try:
        response = await middleware.intercept_message(
            session_id=payload.session_id,
            customer_id=payload.customer_id,
            text=payload.message,
            telemetry_data=payload.telemetry_data,
            metadata=payload.metadata,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
