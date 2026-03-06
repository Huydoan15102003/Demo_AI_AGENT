# AI Chat Service

A FastAPI-based AI chat service using OpenAI Agents SDK with real-time streaming (SSE) and PostgreSQL for persistent chat history.

---

## 1. Prerequisites

- **Docker** and **Docker Compose**
- **OpenAI API key** (for the AI agent)

---

## 2. How to Run the Project

### Step 1: Clone and go to the project folder

```bash
cd /path/to/Demo_AI_AGENT
```

### Step 2: Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:

```
OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Start the service

```bash
docker compose up --build
```

Wait until you see something like:

- `database system is ready to accept connections`
- `Running migrations...`
- `Uvicorn running on http://0.0.0.0:8000`

**Note:** On startup, the API container runs `alembic upgrade head` automatically, so the full database schema is created without running migrations by hand. If a migration fails (e.g. due to an old revision in the DB), the startup script will reset the DB and re-apply migrations.

### Step 4: Verify it’s running

- **API**: http://localhost:8000  
- **Interactive docs**: http://localhost:8000/docs  
- **Health check**:

```bash
curl http://localhost:8000/api/v1/health
```

You should get a successful response (e.g. `200 OK`).

---

## 3. Try the API

### Quick test — stream a chat message

```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000", "user_id": "user-123", "message": "Hello! My name is Alex."}'
```

### Test conversation memory

```bash
# First message
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000", "user_id": "user-123", "message": "Hello! My name is Alex."}'

# Second message (should remember the name)
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000", "user_id": "user-123", "message": "What is my name?"}'
```

### Get session history

```bash
curl "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/history?user_id=user-123"
```

### Delete a session

```bash
curl -X DELETE "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000?user_id=user-123"
```

Use any valid UUID for `session_id`; use the same `session_id` and `user_id` to continue a conversation.

---

## 4. API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/chat/stream` | Send a message and stream the AI response (SSE) |
| `GET` | `/api/v1/sessions/{session_id}/history?user_id=...` | Get full message history for a session |
| `DELETE` | `/api/v1/sessions/{session_id}?user_id=...` | Delete a session and its messages |
| `GET` | `/api/v1/health` | Health check |

**Chat stream request body:**

```json
{
  "session_id": "uuid",
  "user_id": "user-123",
  "message": "Your message here"
}
```

**SSE events:** `agent.message.delta`, `agent.message.done`, `agent.workflow.failed`, `heartbeat` (every 15s).

Full interactive docs: http://localhost:8000/docs

---

## 5. Check Database (optional)

```bash
# List tables
docker exec -it chat_postgres psql -U chat -d chatdb -c "\dt"

# View sessions
docker exec -it chat_postgres psql -U chat -d chatdb -c "SELECT * FROM chat_sessions;"

# View messages
docker exec -it chat_postgres psql -U chat -d chatdb -c "SELECT role, content, created_at FROM chat_messages ORDER BY created_at;"

# Count messages by role
docker exec -it chat_postgres psql -U chat -d chatdb -c "SELECT role, COUNT(*) FROM chat_messages GROUP BY role;"
```

---

## 6. Development (optional)

```bash
# View API logs
docker compose logs -f api

# Open PostgreSQL shell
docker exec -it chat_postgres psql -U chat -d chatdb

# After changing models: create migration and apply
docker exec -it chat_api alembic revision --autogenerate -m "Your changes"
docker exec -it chat_api alembic upgrade head
```

---

## 7. Project Structure

```
app/
├── main.py              # FastAPI app
├── agent.py             # OpenAI Agents SDK
├── database.py          # DB connection
├── models.py            # SQLAlchemy models
├── services/
│   └── database_service.py
└── api/v1/
    ├── router.py
    ├── chat.py          # Chat streaming + persistence
    ├── sessions.py      # Session history & delete
    └── health.py
alembic/                 # Migrations (auto-recovery on startup)
```

---

## Features

- **AI Agent**: OpenAI Agents SDK, streaming responses  
- **Real-time**: SSE streaming  
- **Persistent chat**: PostgreSQL, scoped by user and session  
- **Migrations**: Alembic with auto-recovery when starting via Docker  
