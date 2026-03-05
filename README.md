# AI Chat Service

FastAPI + OpenAI Agents SDK + PostgreSQL + SSE streaming

## Quick Start

```bash
# 1. Run containers
docker compose up --build

# 2. Setup database (first time only)
docker exec -it demo_ai_agent-api-1 bash
alembic init alembic
python setup_alembic.py
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
exit

# 3. Check database
docker exec -it demo_ai_agent-postgres-1 psql -U chat -d chatdb
\dt
\q
```

**Access:**
- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs
- Database: localhost:5432 (user: `chat`, db: `chatdb`)

## Development

```bash
# After changing models:
docker exec -it demo_ai_agent-api-1 alembic revision --autogenerate -m "Your changes"
docker exec -it demo_ai_agent-api-1 alembic upgrade head
```

## Project Structure

```
app/
  main.py           # FastAPI app
  database.py       # Database config
  models.py         # SQLAlchemy models
  api/v1/           # API endpoints (health, chat, sessions)
alembic/            # Database migrations
```