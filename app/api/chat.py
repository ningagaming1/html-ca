from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.agent.runner import stream_fitbuddy

router = APIRouter(prefix="/api", tags=["AI Assistant"])

class ChatRequest(BaseModel):
    message: str
    user_name: Optional[str] = "Member"
    user_role: Optional[str] = "member"
    user_context: Optional[str] = ""
    stream: Optional[bool] = False

@router.post("/chat")
def chat_endpoint(payload: ChatRequest):
    if payload.stream:
        def event_stream():
            for chunk in stream_fitbuddy(
                user_message=payload.message,
                user_name=payload.user_name,
                user_role=payload.user_role,
                user_context=payload.user_context
            ):
                yield chunk

        return StreamingResponse(event_stream(), media_type="text/plain")
    else:
        full_reply = "".join(list(stream_fitbuddy(
            user_message=payload.message,
            user_name=payload.user_name,
            user_role=payload.user_role,
            user_context=payload.user_context
        )))
        return {
            "status": "success",
            "reply": full_reply
        }
