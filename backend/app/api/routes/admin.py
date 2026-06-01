"""Admin utilities (database backup)."""
import json
from datetime import datetime, timezone

from bson import json_util
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.core.config import settings
from app.db.repositories import export_database_backup, save_database_backup_to_disk

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/backup/status")
async def backup_status() -> dict:
    """Whether server-side backup directory is configured."""
    return {
        "backupDirConfigured": bool(settings.backup_dir),
        "backupDir": settings.backup_dir,
    }


@router.get("/backup")
async def download_backup() -> Response:
    """Download a JSON snapshot of all MongoDB BDSA collections."""
    backup = await export_database_backup()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"bdsa-backup-{stamp}.json"
    content = json.dumps(backup, default=json_util.default, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/backup/save")
async def save_backup_on_server() -> dict:
    """Write backup JSON to BDSA_BACKUP_DIR (or BACKUP_DIR in env)."""
    if not settings.backup_dir:
        raise HTTPException(
            status_code=400,
            detail="Server backup directory not configured. Set BDSA_BACKUP_DIR on the API container.",
        )
    return await save_database_backup_to_disk(settings.backup_dir)
