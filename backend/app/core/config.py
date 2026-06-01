"""Application configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from environment."""

    app_name: str = "BDSA Protocols API"
    debug: bool = False

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "bdsa_protocols"

    # Optional directory for server-side JSON backups (POST /api/admin/backup/save).
    backup_dir: str | None = None

    # DSA/Girder (optional; used for sync endpoint). Read from DSA_API_URL / DSA_API_KEY in .env.
    dsa_api_url: str | None = Field(default=None, validation_alias="DSA_API_URL")
    dsa_api_key: str | None = Field(default=None, validation_alias="DSA_API_KEY")

    model_config = {
        "env_prefix": "BDSA_",
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
