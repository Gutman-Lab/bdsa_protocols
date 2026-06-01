"""Girder/DSA helpers: list folders and recursively fetch items (mirrors dsa_helpers.girder_utils pattern)."""
from __future__ import annotations

import asyncio
from typing import Any

from girder_client import GirderClient

from app.core.config import settings


def _get_items_sync(gc: GirderClient, parent_id: str) -> list[dict[str, Any]]:
    """Get all items under a folder recursively (Girder resource API, type=folder, limit=0)."""
    params = {"type": "folder", "limit": 0, "offset": 0, "sort": "_id", "sortdir": 1}
    try:
        return gc.get(f"resource/{parent_id}/items", parameters=params)
    except Exception:
        params["type"] = "collection"
        return gc.get(f"resource/{parent_id}/items", parameters=params)


def _list_folder_sync(gc: GirderClient, folder_id: str) -> list[dict[str, Any]]:
    """List direct subfolders of a folder."""
    return list(gc.listFolder(folder_id))


def _authenticate_sync() -> GirderClient | None:
    """Return authenticated Girder client or None if DSA config missing."""
    if not settings.dsa_api_url or not settings.dsa_api_key:
        return None
    gc = GirderClient(apiUrl=settings.dsa_api_url)
    gc.authenticate(apiKey=settings.dsa_api_key)
    return gc


async def get_authenticated_client() -> GirderClient | None:
    """Return authenticated Girder client (run in thread to avoid blocking)."""
    return await asyncio.to_thread(_authenticate_sync)


async def fetch_items_for_folder(gc: GirderClient, folder_id: str) -> list[dict[str, Any]]:
    """Recursively fetch all items under a folder. Runs in thread pool."""
    return await asyncio.to_thread(_get_items_sync, gc, folder_id)


async def fetch_collection_from_girder(
    gc: GirderClient, root_folder_id: str
) -> list[dict[str, Any]]:
    """
    Hierarchy: root -> year folders -> case folders -> items.
    List subfolders of root (year folders), then for each year list its subfolders (case IDs).
    For each case folder, recursively get all items and tag with case_fld_id and year_fld_id.
    Returns a flat list of item dicts with case_fld_id = case folder _id, year_fld_id = year folder _id.
    """
    year_folders = await asyncio.to_thread(_list_folder_sync, gc, root_folder_id)
    all_items: list[dict[str, Any]] = []
    for year_folder in year_folders:
        year_fld_id = year_folder["_id"]
        case_folders = await asyncio.to_thread(_list_folder_sync, gc, year_fld_id)
        for case_folder in case_folders:
            case_fld_id = case_folder["_id"]
            case_fld_name = case_folder.get("name") or ""
            items = await fetch_items_for_folder(gc, case_fld_id)
            for item in items:
                item = dict(item)
                item["case_fld_id"] = case_fld_id
                item["case_fld_name"] = case_fld_name
                item["year_fld_id"] = year_fld_id
                all_items.append(item)
    return all_items
