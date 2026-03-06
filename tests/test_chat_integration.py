"""Integration tests - verify messages persisted to DB with real test DB, mock LLM."""

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4, UUID
import pytest
from sqlalchemy import select

from app.models import ChatSession, ChatMessage, MessageRole
from app.services.database_service import DatabaseService


class MockStreamEvent:
    """Mock event from agent streaming."""
    def __init__(self, event_type="raw_response_event", delta=None):
        self.type = event_type
        self.data = MockEventData(delta)


class MockEventData:
    """Mock event data with delta."""
    def __init__(self, delta):
        self.delta = delta


class MockAgentResult:
    """Mock agent stream result."""
    def __init__(self, response_text):
        self.response_text = response_text
        # Split response into chunks for realistic streaming (include spaces)
        self.deltas = list(response_text)
    
    async def stream_events(self):
        """Mock stream_events that yields character-by-character."""
        import asyncio
        for delta in self.deltas:
            yield MockStreamEvent("raw_response_event", delta)
            await asyncio.sleep(0.001)  # Small delay to simulate streaming


@pytest.mark.asyncio
@patch('app.api.v1.chat.run_agent_stream')
async def test_messages_persisted_to_database(mock_run_agent, test_client_with_db, test_db):
    """Integration test: Verify messages are correctly persisted to database."""
    
    # Setup - use test UUID prefix for cleanup (11111111-)
    session_id = UUID("11111111-3333-3333-3333-333333333333")
    user_id = "integration-test-user"
    user_message = "What is the capital of France?"
    agent_response = "The capital of France is Paris."
    
    # Mock agent response
    mock_agent_result = MockAgentResult(agent_response)
    mock_run_agent.return_value = mock_agent_result
    
    # Make request
    payload = {
        "session_id": str(session_id),
        "user_id": user_id,
        "message": user_message
    }
    
    response = test_client_with_db.post(
        "/api/v1/chat/stream",
        json=payload,
        headers={"Accept": "text/event-stream"}
    )
    
        # Verify HTTP response
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
    assert response.status_code == 200
    
    # Verify session was created in database
    session = await DatabaseService.get_session_history(test_db, session_id, user_id)
    assert session is not None, "Session should be created in database"
    assert session.user_id == user_id
    assert session.id == session_id
    
    # Verify messages were saved to database
    result = await test_db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    
    assert len(messages) == 2, f"Should have 2 messages (user + assistant), got {len(messages)}"
    
    # Verify user message
    user_msg = messages[0]
    assert user_msg.role == MessageRole.USER
    assert user_msg.content == user_message
    assert user_msg.session_id == session_id
    
    # Verify assistant message  
    assistant_msg = messages[1]
    assert assistant_msg.role == MessageRole.ASSISTANT
    assert assistant_msg.content == agent_response
    assert assistant_msg.session_id == session_id
    
    # Verify timestamp order
    assert user_msg.created_at <= assistant_msg.created_at


@pytest.mark.asyncio
@patch('app.api.v1.chat.run_agent_stream')
async def test_conversation_history_with_database(mock_run_agent, test_client_with_db, test_db):
    """Integration test: Verify conversation history is loaded from DB and passed to agent."""
    
    # Setup - use test UUID prefix for cleanup (11111111-)
    session_id = UUID("11111111-4444-4444-4444-444444444444")
    user_id = "integration-test-user"
    
    # First conversation turn
    first_message = "Hello! My name is Bob."
    first_response = "Nice to meet you, Bob!"
    
    mock_agent_result_1 = MockAgentResult(first_response)
    mock_run_agent.return_value = mock_agent_result_1
    
    payload_1 = {
        "session_id": str(session_id),
        "user_id": user_id,
        "message": first_message
    }
    
    response_1 = test_client_with_db.post(
        "/api/v1/chat/stream",
        json=payload_1,
        headers={"Accept": "text/event-stream"}
    )
    assert response_1.status_code == 200
    
    # Reset mock to capture second call
    mock_run_agent.reset_mock()
    
    # Second conversation turn - should include history
    second_message = "What is my name?"
    second_response = "Your name is Bob!"
    
    mock_agent_result_2 = MockAgentResult(second_response)
    mock_run_agent.return_value = mock_agent_result_2
    
    payload_2 = {
        "session_id": str(session_id),
        "user_id": user_id,
        "message": second_message
    }
    
    response_2 = test_client_with_db.post(
        "/api/v1/chat/stream",
        json=payload_2,
        headers={"Accept": "text/event-stream"}
    )
    assert response_2.status_code == 200
    
    # Verify agent was called with conversation history
    mock_run_agent.assert_called_once()
    conversation_messages = mock_run_agent.call_args[0][0]
    
    assert len(conversation_messages) == 3, "Should have 3 messages: user1, assistant1, user2"
    
    # Check first user message
    assert conversation_messages[0]["role"] == "user"
    assert conversation_messages[0]["content"] == first_message
    
    # Check first assistant message  
    assert conversation_messages[1]["role"] == "assistant"
    assert conversation_messages[1]["content"] == first_response
    
    # Check second user message
    assert conversation_messages[2]["role"] == "user"
    assert conversation_messages[2]["content"] == second_message
    
    # Verify all 4 messages are in database
    result = await test_db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    all_messages = result.scalars().all()
    assert len(all_messages) == 4, "Should have 4 messages in database"
    
    # Verify message order and content
    assert all_messages[0].role == MessageRole.USER
    assert all_messages[0].content == first_message
    assert all_messages[1].role == MessageRole.ASSISTANT  
    assert all_messages[1].content == first_response
    assert all_messages[2].role == MessageRole.USER
    assert all_messages[2].content == second_message
    assert all_messages[3].role == MessageRole.ASSISTANT
    assert all_messages[3].content == second_response


@pytest.mark.asyncio
async def test_session_isolation_between_users(test_client_with_db, test_db):
    """Integration test: Verify users can only access their own sessions."""
    
    session_id = UUID("11111111-5555-5555-5555-555555555555")
    user1_id = "user1"
    user2_id = "user2"
    
    # User 1 creates a session
    with patch('app.api.v1.chat.run_agent_stream') as mock_agent:
        mock_agent.return_value = MockAgentResult("Hello user1!")
        
        payload = {
            "session_id": str(session_id),
            "user_id": user1_id,
            "message": "Hello from user1"
        }
        
        response = test_client_with_db.post(
            "/api/v1/chat/stream",
            json=payload,
            headers={"Accept": "text/event-stream"}
        )
        assert response.status_code == 200
    
    # User 2 tries to access the same session - should get 403
    with patch('app.api.v1.chat.run_agent_stream') as mock_agent:
        mock_agent.return_value = MockAgentResult("Hello user2!")
        
        payload = {
            "session_id": str(session_id),
            "user_id": user2_id,
            "message": "Hello from user2"
        }
        
        response = test_client_with_db.post(
            "/api/v1/chat/stream",
            json=payload,
            headers={"Accept": "text/event-stream"}
        )
        assert response.status_code == 403, "User 2 should not access user 1's session"
    
    # Verify only user1's message is in database
    result = await test_db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    messages = result.scalars().all()
    
    # Should only have user1's messages (1 user + 1 assistant)
    assert len(messages) == 2
    
    # Get the session to verify user
    session = await DatabaseService.get_session_history(test_db, session_id, user1_id)
    assert session is not None
    assert session.user_id == user1_id


@pytest.mark.asyncio
async def test_session_history_endpoint_integration(test_client_with_db, session_with_messages):
    """Integration test: Verify session history endpoint works with real DB."""
    
    session = session_with_messages
    
    # Get session history via API
    response = test_client_with_db.get(
        f"/api/v1/sessions/{session.id}/history?user_id={session.user_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["session_id"] == str(session.id)
    assert data["user_id"] == session.user_id
    assert len(data["messages"]) == 2
    
    # Verify message order and content
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello! My name is Alice."
    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][1]["content"] == "Nice to meet you, Alice!"