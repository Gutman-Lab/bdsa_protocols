"""MongoDB connection and database access."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def get_client() -> AsyncIOMotorClient:
    """Get or create the MongoDB client."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client


async def get_db() -> AsyncIOMotorDatabase:
    """Get the application database."""
    global _db
    if _db is None:
        client = await get_client()
        _db = client[settings.mongodb_db]
    return _db


async def close_db() -> None:
    """Close MongoDB connection (for shutdown)."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
