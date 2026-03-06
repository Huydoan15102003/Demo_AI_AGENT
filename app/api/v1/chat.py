import json
import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import run_agent_stream
from app.database import get_db
from app.models import MessageRole
from app.services.database_service import DatabaseService

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    session_id: UUID
    user_id: str
    message: str

@router.post("/stream")
async def chat_stream(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Stream AI response via SSE."""
    try:
        # 1. Get or create session
        session = await DatabaseService.get_or_create_session(
            db, payload.session_id, payload.user_id
        )
        
        # 2. Save user message
        await DatabaseService.save_message(
            db, session.id, MessageRole.USER, payload.message
        )
        
        # 3. Run agent streaming
        run_result = run_agent_stream(payload.message)

        async def event_generator():
            assistant_response = ""
            error_occurred = False
            last_heartbeat = asyncio.get_event_loop().time()
            
            try:
                async for event in run_result.stream_events():
                    # Handle text deltas from agent
                    if hasattr(event, 'type') and event.type == "raw_response_event":
                        if hasattr(event.data, 'delta') and event.data.delta:
                            text_chunk = event.data.delta
                            assistant_response += text_chunk
                            
                            yield "event: agent.message.delta\n"
                            yield f'data: {json.dumps({"text": text_chunk})}\n\n'
                    
                    # Send heartbeat every 15 seconds
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat > 15:
                        yield "event: heartbeat\n"
                        yield f'data: {json.dumps({"timestamp": current_time})}\n\n'
                        last_heartbeat = current_time
                
                # 4. Save assistant response to DB
                if assistant_response.strip():
                    await DatabaseService.save_message(
                        db, session.id, MessageRole.ASSISTANT, assistant_response
                    )
                    
                    # Update session timestamp
                    await DatabaseService.update_session_timestamp(
                        db, session.id, payload.user_id
                    )
                
                # Send completion
                yield "event: agent.message.done\n"
                yield f'data: {json.dumps({"session_id": str(payload.session_id)})}\n\n'
                
            except Exception as e:
                error_occurred = True
                yield "event: agent.workflow.failed\n"
                yield f'data: {json.dumps({"error": str(e)})}\n\n'

        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except ValueError as e:
        # Session ownership error
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat streaming failed: {str(e)}")

