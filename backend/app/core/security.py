"""Optional shared API key for /api routes."""
import logging

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import settings

logger = logging.getLogger(__name__)

API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


async def require_api_key(key: str | None = Security(api_key_header)) -> None:
    """Reject requests when BDSA_API_KEY is configured and the header is missing or wrong."""
    if not settings.api_key:
        return
    if not key or key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or missing API key. Send header {API_KEY_HEADER}.",
        )


def log_api_key_status() -> None:
    if settings.api_key:
        logger.info("API key auth enabled for /api routes")
    else:
        logger.warning(
            "BDSA_API_KEY is not set — /api routes accept unauthenticated requests"
        )
