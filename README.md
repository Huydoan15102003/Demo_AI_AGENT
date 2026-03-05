# AI Chat Service

Take-home: FastAPI + OpenAI Agents SDK + PostgreSQL + SSE streaming.

## RUN (development)

```bash
cd Demo_AI_AGENT
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Docker

```bash
docker compose up --build
```

- API: http://127.0.0.1:8000
- Postgres: localhost:5432 (user `chat`, db `chatdb`)

## Structre

```
app/
  main.py           # FastAPI app
  api/v1/
    router.py       # Mount /api/v1
    health.py       # GET /api/v1/health
    chat.py         # POST /api/v1/chat/stream (stub)
    sessions.py     # GET/DELETE /api/v1/sessions/{id}... (stub)
```