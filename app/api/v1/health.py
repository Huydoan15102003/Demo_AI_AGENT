from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Health check — returns 200 OK."""
    return {"status": "ok"}
