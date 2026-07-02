from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


mongo_client: AsyncIOMotorClient | None = None
mongo_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global mongo_client, mongo_db

    if mongo_client is not None and mongo_db is not None:
        return

    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    mongo_db = mongo_client[settings.mongodb_db_name]

    await mongo_db.users.create_index("email", unique=True)
    await mongo_db.users.create_index("username", unique=True)
    await mongo_db.ocr_drafts.create_index([("feature", 1), ("created_at", -1)])
    await mongo_db.split_bills.create_index([("owner_id", 1), ("created_at", -1)])


async def close_mongo_connection() -> None:
    global mongo_client, mongo_db

    if mongo_client is not None:
        mongo_client.close()

    mongo_client = None
    mongo_db = None


def get_database() -> AsyncIOMotorDatabase:
    if mongo_db is None:
        raise RuntimeError("MongoDB connection is not initialized")
    return mongo_db
