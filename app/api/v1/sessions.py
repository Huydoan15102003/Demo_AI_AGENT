from fastapi import APIRouter

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}/history")
async def get_session_history(session_id: str, user_id: str):
    """Return full message history for a session. (Stub.)"""
    # TODO: filter by session_id + user_id, return messages
    return {"session_id": session_id, "messages": []}


@router.delete("/{session_id}")
async def delete_session(session_id: str, user_id: str):
    """Delete session and all its messages. (Stub.)"""
    # TODO: delete only if session belongs to user_id
    return {"deleted": session_id}
