"""Database service for chat operations."""

import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ChatSession, ChatMessage, MessageRole


class DatabaseService:
    """Service for database operations."""

    @staticmethod
    async def get_or_create_session(
        db: AsyncSession, session_id: UUID, user_id: str
    ) -> ChatSession:
        """Get existing session or create new one."""
        # First, check if session exists with this ID
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        existing_session = result.scalar_one_or_none()
        
        if existing_session:
            # Session exists - check ownership
            if existing_session.user_id != user_id:
                raise ValueError(f"Session {session_id} belongs to different user")
            return existing_session
        
        # Session doesn't exist - create new one
        try:
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
            
        except Exception as e:
            # Rollback in case of any error
            await db.rollback()
            raise e

    @staticmethod
    async def save_message(
        db: AsyncSession, 
        session_id: UUID, 
        role: MessageRole, 
        content: str
    ) -> ChatMessage:
        """Save a message to database."""
        message = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.utcnow()
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_session_history(
        db: AsyncSession, session_id: UUID, user_id: str
    ) -> Optional[ChatSession]:
        """Get session with all messages."""
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_session(
        db: AsyncSession, session_id: UUID, user_id: str
    ) -> bool:
        """Delete session and all its messages."""
        # First check if session exists and belongs to user
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        # Delete messages first (cascade should handle this, but being explicit)
        await db.execute(
            delete(ChatMessage).where(ChatMessage.session_id == session_id)
        )
        
        # Delete session
        await db.execute(
            delete(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        
        await db.commit()
        return True

    @staticmethod
    async def update_session_timestamp(
        db: AsyncSession, session_id: UUID, user_id: str
    ) -> None:
        """Update session's updated_at timestamp."""
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.updated_at = datetime.utcnow()
            await db.commit()