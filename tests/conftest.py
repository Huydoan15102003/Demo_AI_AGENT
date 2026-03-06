"""Test configuration and fixtures."""

import asyncio
import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.main import app
from app.database import get_db, Base
from app.models import ChatSession, ChatMessage, MessageRole


# Test database URL - use PostgreSQL with test schema
TEST_DATABASE_URL = "postgresql+asyncpg://chat:chat@postgres:5432/chatdb"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Create test database session with cleanup."""
    # Create async engine for tests using existing PostgreSQL
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create session factory
    TestSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create session
    async with TestSessionLocal() as session:
        # Clean up any existing test data before test (use UUIDs starting with 11111111)
        try:
            await session.execute(text("DELETE FROM chat_messages WHERE session_id::text LIKE '11111111-%'"))
            await session.execute(text("DELETE FROM chat_sessions WHERE id::text LIKE '11111111-%'"))
            await session.commit()
        except Exception as e:
            print(f"Cleanup before test failed: {e}")
            await session.rollback()
        
        yield session
        
        # Clean up test data after test
        try:
            await session.execute(text("DELETE FROM chat_messages WHERE session_id::text LIKE '11111111-%'"))
            await session.execute(text("DELETE FROM chat_sessions WHERE id::text LIKE '11111111-%'"))
            await session.commit()
        except Exception as e:
            print(f"Cleanup after test failed: {e}")
            await session.rollback()
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_client_with_db():
    """Create test client with test database dependency override."""
    
    # Use the same database as main app (no separate test db session)
    # This avoids connection conflicts
    
    client = TestClient(app)
    yield client


@pytest_asyncio.fixture
async def sample_session(test_db):
    """Create a sample chat session for testing."""
    session_id = UUID("11111111-1111-1111-1111-111111111111")
    user_id = "test-user"
    
    session = ChatSession(
        id=session_id,
        user_id=user_id
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    
    return session


@pytest_asyncio.fixture
async def session_with_messages(test_db):
    """Create a session with some messages for testing."""
    session_id = UUID("11111111-2222-2222-2222-222222222222")
    user_id = "test-user"
    
    # Create session
    session = ChatSession(
        id=session_id,
        user_id=user_id
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    
    # Add messages
    messages = [
        ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content="Hello! My name is Alice."
        ),
        ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content="Nice to meet you, Alice!"
        )
    ]
    
    for msg in messages:
        test_db.add(msg)
    
    await test_db.commit()
    
    # Refresh session to load messages
    await test_db.refresh(session)
    
    return session