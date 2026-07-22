"""MongoDB helpers for NACC clinical records keyed by NACCID."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.mongodb import get_db

COLLECTION = "clinical_by_nacc"
_index_ensured = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def ensure_clinical_indexes() -> None:
    """Create unique index on naccid (idempotent)."""
    global _index_ensured
    if _index_ensured:
        return
    db = await get_db()
    await db[COLLECTION].create_index("naccid", unique=True)
    _index_ensured = True


async def get_clinical_by_nacc(naccid: str) -> dict[str, Any] | None:
    """Return clinical document for a NACCID, or None if missing."""
    await ensure_clinical_indexes()
    db = await get_db()
    doc = await db[COLLECTION].find_one({"naccid": naccid.strip()})
    if doc is None:
        return None
    doc.pop("_id", None)
    return doc


async def get_clinical_stats() -> dict[str, Any]:
    """Return simple counts for the clinical collection."""
    await ensure_clinical_indexes()
    db = await get_db()
    count = await db[COLLECTION].count_documents({})
    return {"count": count}


async def upsert_clinical_by_nacc(doc: dict[str, Any]) -> dict[str, Any]:
    """Upsert one clinical document. Requires ``naccid`` and ``clinical``."""
    await ensure_clinical_indexes()
    naccid = str(doc["naccid"]).strip()
    payload = {
        "naccid": naccid,
        "clinical": doc.get("clinical") or {},
        "source": doc.get("source", "investigator_nacc74"),
        "visitMeta": doc.get("visitMeta") or {},
        "lastUpdated": _now_iso(),
    }
    db = await get_db()
    await db[COLLECTION].update_one(
        {"naccid": naccid},
        {"$set": payload},
        upsert=True,
    )
    return payload


async def bulk_upsert_clinical_by_nacc(docs: list[dict[str, Any]]) -> int:
    """Upsert many clinical documents. Returns number of upserts attempted."""
    if not docs:
        return 0
    await ensure_clinical_indexes()
    from pymongo import UpdateOne

    db = await get_db()
    now = _now_iso()
    ops: list[UpdateOne] = []
    for doc in docs:
        naccid = str(doc["naccid"]).strip()
        payload = {
            "naccid": naccid,
            "clinical": doc.get("clinical") or {},
            "source": doc.get("source", "investigator_nacc74"),
            "visitMeta": doc.get("visitMeta") or {},
            "lastUpdated": now,
        }
        ops.append(
            UpdateOne({"naccid": naccid}, {"$set": payload}, upsert=True)
        )
    if not ops:
        return 0
    result = await db[COLLECTION].bulk_write(ops, ordered=False)
    return result.upserted_count + result.modified_count
