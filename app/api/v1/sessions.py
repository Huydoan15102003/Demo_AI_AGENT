from fastapi import APIRouter

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("/{session_id}/history")
async def get_session_history(session_id: str, user_id: str):
    """Return session history (stub - use existing DB logic)."""
    return {"session_id": session_id, "messages": []}

@router.delete("/{session_id}")
async def delete_session(session_id: str, user_id: str):
    """Delete session (stub - use existing DB logic)."""
    return {"deleted": session_id}
