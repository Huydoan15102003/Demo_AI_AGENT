from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream():
    """Accept user message, run agent, stream response via SSE. (Stub.)"""
    # TODO: request body session_id, user_id, message
    # TODO: SSE stream agent.message.delta, agent.message.done, etc.
    return {"message": "stub"}
