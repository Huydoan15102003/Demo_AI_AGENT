"""Simplified integration test to debug issues."""

import json
from unittest.mock import patch
from uuid import UUID
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
    def __init__(self, response_text):
        self.response_text = response_text
        # Split response into chunks for realistic streaming (include spaces)
        self.deltas = list(response_text)
    
    async def stream_events(self):
        """Mock stream_events that yields character-by-character."""
        import asyncio
        for delta in self.deltas:
            yield MockStreamEvent("raw_response_event", delta)
            await asyncio.sleep(0.001)


def test_health_endpoint(test_client):
    """Test health endpoint works."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200


@patch('app.api.v1.chat.run_agent_stream')
def test_chat_endpoint_basic(mock_run_agent, test_client):
    """Test basic chat endpoint without DB assertions."""
    
    # Mock agent response
    mock_agent_result = MockAgentResult("Hello!")
    mock_run_agent.return_value = mock_agent_result
    
    # Make request
    payload = {
        "session_id": "11111111-7777-7777-7777-777777777777",
        "user_id": "test-user",
        "message": "Hello"
    }
    
    response = test_client.post(
        "/api/v1/chat/stream",
        json=payload,
        headers={"Accept": "text/event-stream"}
    )
    
    # Debug response
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Text: {response.text}")
    
    # Basic assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"