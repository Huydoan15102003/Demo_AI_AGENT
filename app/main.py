from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="AI Chat Service",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"service": "AI Chat Service", "docs": "/docs"}
