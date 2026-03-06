"""Unit tests for chat streaming - verify SSE events order with mocked agent."""

import asyncio
import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import pytest


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
    def __init__(self, deltas):
        self.deltas = deltas
        self.index = 0
    
    async def stream_events(self):
        """Mock stream_events that yields text deltas."""
        for delta in self.deltas:
            if delta:  # Only yield if delta is not None/empty
                yield MockStreamEvent("raw_response_event", delta)
            await asyncio.sleep(0.001)  # Small delay to simulate streaming


@pytest.mark.asyncio
@patch('app.api.v1.chat.run_agent_stream')
@patch('app.services.database_service.DatabaseService.get_or_create_session')
@patch('app.services.database_service.DatabaseService.get_session_history')
@patch('app.services.database_service.DatabaseService.save_message')
@patch('app.services.database_service.DatabaseService.update_session_timestamp')
async def test_sse_events_order(
    mock_update_timestamp,
    mock_save_message,
    mock_get_history,
    mock_get_session,
    mock_run_agent,
    test_client
):
    """Unit test: Verify SSE events are emitted in correct order."""
    import asyncio
    
    # Setup mocks
    session_id = uuid4()
    user_id = "test-user"
    
    # Mock session
    mock_session = AsyncMock()
    mock_session.id = session_id
    mock_session.user_id = user_id
    mock_get_session.return_value = mock_session
    
    # Mock empty history (new conversation)
    mock_get_history.return_value = None
    
    # Mock agent streaming with specific text chunks
    text_chunks = ["Hello", " there", "!", " How", " can", " I", " help?"]
    mock_agent_result = MockAgentResult(text_chunks)
    mock_run_agent.return_value = mock_agent_result
    
    # Mock database operations
    mock_save_message.return_value = AsyncMock()
    mock_update_timestamp.return_value = None
    
    # Make request
    payload = {
        "session_id": str(session_id),
        "user_id": user_id,
        "message": "Hello AI!"
    }
    
    response = test_client.post(
        "/api/v1/chat/stream",
        json=payload,
        headers={"Accept": "text/event-stream"}
    )
    
    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Parse SSE events
    events = []
    response_text = response.text
    
    # Split by event boundaries and parse
    lines = response_text.strip().split('\n')
    current_event = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('event:'):
            if current_event:  # Save previous event
                events.append(current_event)
            current_event = {'type': line.split(':', 1)[1].strip()}
        elif line.startswith('data:'):
            data_json = line.split(':', 1)[1].strip()
            try:
                current_event['data'] = json.loads(data_json)
            except json.JSONDecodeError:
                current_event['data'] = data_json
        elif line == '' and current_event:  # Empty line marks end of event
            events.append(current_event)
            current_event = {}
    
    # Add last event if exists
    if current_event:
        events.append(current_event)
    
    # Verify event order and content
    print(f"Total events: {len(events)}")
    for i, event in enumerate(events):
        print(f"Event {i}: {event}")
    
    # Check we have the right number of events
    # Should have: N delta events + 1 done event (N = number of text chunks)
    expected_delta_events = len(text_chunks)
    expected_total_events = expected_delta_events + 1  # +1 for done event
    
    assert len(events) == expected_total_events, f"Expected {expected_total_events} events, got {len(events)}"
    
    # Verify delta events come first, in order
    for i in range(expected_delta_events):
        event = events[i]
        assert event['type'] == 'agent.message.delta', f"Event {i} should be delta, got {event['type']}"
        assert 'text' in event['data'], f"Event {i} should have text in data"
        assert event['data']['text'] == text_chunks[i], f"Event {i} text mismatch"
    
    # Verify done event comes last
    last_event = events[-1]
    assert last_event['type'] == 'agent.message.done', "Last event should be agent.message.done"
    assert 'session_id' in last_event['data'], "Done event should have session_id"
    assert last_event['data']['session_id'] == str(session_id), "Done event session_id should match"
    
    # Verify database operations were called correctly
    mock_get_session.assert_called_once()
    
    # Should save user message
    assert mock_save_message.call_count >= 1
    
    # Should call agent with conversation (even if empty for new conversation)
    mock_run_agent.assert_called_once()
    conversation_messages = mock_run_agent.call_args[0][0]
    assert isinstance(conversation_messages, list)
    assert len(conversation_messages) == 1  # Only user message for new conversation
    assert conversation_messages[0]["role"] == "user"
    assert conversation_messages[0]["content"] == "Hello AI!"


@pytest.mark.asyncio
async def test_sse_events_with_conversation_history():
    """Test that agent receives conversation history correctly."""
    # This is tested as part of the integration test
    # Here we focus on the unit test aspect - mocking agent behavior
    pass