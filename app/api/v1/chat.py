import json
from uuid import UUID
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agent import run_agent_stream

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    session_id: UUID
    user_id: str
    message: str

@router.post("/stream")
async def chat_stream(payload: ChatRequest):
    """Stream AI response via SSE."""
    run_result = run_agent_stream(payload.message)

    async def event_generator():
        assistant_response = ""
        
        async for event in run_result.stream_events():
            # Handle text deltas from agent
            if hasattr(event, 'type') and event.type == "raw_response_event":
                if hasattr(event.data, 'delta') and event.data.delta:
                    text_chunk = event.data.delta
                    assistant_response += text_chunk
                    
                    yield "event: agent.message.delta\n"
                    yield f'data: {json.dumps({"text": text_chunk})}\n\n'

        # Send completion
        yield "event: agent.message.done\n"
        yield f'data: {json.dumps({"session_id": str(payload.session_id)})}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")

