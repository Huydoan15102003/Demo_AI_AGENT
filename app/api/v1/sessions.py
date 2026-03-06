from uuid import UUID
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.database_service import DatabaseService

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("/{session_id}/history")
async def get_session_history(
    session_id: UUID, 
    user_id: str = Query(..., description="User ID to filter session"),
    db: AsyncSession = Depends(get_db)
):
    """Return session history with all messages."""
    try:
        session = await DatabaseService.get_session_history(db, session_id, user_id)
        
        if not session:
            raise HTTPException(
                status_code=404, 
                detail=f"Session {session_id} not found or does not belong to user {user_id}"
            )
        
        # Format response
        messages = []
        for message in sorted(session.messages, key=lambda m: m.created_at):
            messages.append({
                "role": message.role.value,
                "content": message.content,
                "created_at": message.created_at.isoformat()
            })
        
        return {
            "session_id": str(session.id),
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {str(e)}")

@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID, 
    user_id: str = Query(..., description="User ID to verify ownership"),
    db: AsyncSession = Depends(get_db)
):
    """Delete session and all its messages."""
    try:
        deleted = await DatabaseService.delete_session(db, session_id, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=404, 
                detail=f"Session {session_id} not found or does not belong to user {user_id}"
            )
        
        return {"deleted": str(session_id), "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
