from fastapi import APIRouter

from app.core.database import get_database

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    status = {"status": "ok"}

    try:
        database = get_database()
        await database.command("ping")
        status["mongo"] = "ok"
    except Exception:
        status["mongo"] = "down"

    return status
