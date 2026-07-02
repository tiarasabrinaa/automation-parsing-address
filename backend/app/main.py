from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.database import close_mongo_connection, connect_to_mongo
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title=settings.project_name, version=settings.version, lifespan=lifespan)
app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": f"{settings.project_name} is running"
    }
