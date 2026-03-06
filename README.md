# AI Chat Service

A FastAPI-based AI chat service using OpenAI Agents SDK with real-time streaming via Server-Sent Events (SSE) and PostgreSQL for persistent chat history.

## Features

- **AI Agent Integration**: Uses OpenAI Agents SDK for intelligent responses
- **Real-time Streaming**: SSE-based streaming for immediate response feedback
- **Persistent Chat History**: PostgreSQL storage with user/session scoping
- **RESTful API**: Clean API design with proper error handling
- **Database Migrations**: Alembic for schema management

## Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Run with Docker**:
   ```bash
   docker compose up --build
   ```

3. **Access the Service**:
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health

4. **Quick Test**:
   ```bash
   # Test health
   curl http://localhost:8000/api/v1/health
   
   # Test chat streaming
   curl -X POST http://localhost:8000/api/v1/chat/stream \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000", "user_id": "test-user", "message": "Hello AI!"}'
   ```

## API Endpoints

### Chat Streaming
```
POST /api/v1/chat/stream
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "message": "Hello, how are you?"
}

Response: text/event-stream with events:
- agent.message.delta: Text chunks as they arrive
- agent.message.done: Completion with session_id
- agent.workflow.failed: Error handling
- heartbeat: Keep-alive every 15s
```

### Session Management
```
GET /api/v1/sessions/{session_id}/history?user_id=user-123
DELETE /api/v1/sessions/{session_id}?user_id=user-123
```

## Testing with CURL

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Stream Chat (SSE)
```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-123",
    "message": "What is the capital of France?"
  }'
```

### 3. Get Session History
```bash
curl "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/history?user_id=user-123"
```

### 4. Delete Session
```bash
curl -X DELETE "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000?user_id=user-123"
```

### 5. API Documentation
```bash
curl http://localhost:8000/docs
# Or visit in browser: http://localhost:8000/docs
```

## Testing with Postman

1. **Stream Chat**:
   - Method: POST
   - URL: `http://localhost:8000/api/v1/chat/stream`
   - Headers: `Accept: text/event-stream`
   - Body (JSON):
     ```json
     {
       "session_id": "550e8400-e29b-41d4-a716-446655440000",
       "user_id": "user-123", 
       "message": "What is the capital of France?"
     }
     ```

2. **Get History**:
   - Method: GET
   - URL: `http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/history?user_id=user-123`

## Development

```bash
# View logs
docker compose logs -f api

# Access database
docker exec -it chat_postgres psql -U chat -d chatdb

# Run migrations after model changes
docker exec -it chat_api alembic revision --autogenerate -m "Your changes"
docker exec -it chat_api alembic upgrade head
```

## Project Structure

```
app/
├── main.py              # FastAPI application
├── agent.py             # OpenAI Agents SDK configuration
├── database.py          # Database connection setup
├── models.py            # SQLAlchemy models
├── exceptions.py        # Custom exceptions
├── services/
│   └── database_service.py  # Database operations
└── api/v1/
    ├── router.py        # API router setup
    ├── chat.py          # Chat streaming endpoint
    ├── sessions.py      # Session management
    └── health.py        # Health check
alembic/                 # Database migrations
tests/                   # Test suite (TODO)
```