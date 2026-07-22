"""Validation for collection-level block (blocking) protocols."""
from __future__ import annotations

from typing import Any


def normalize_block_slots(block: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize slots from block protocol document."""
    slots = block.get("slots")
    if isinstance(slots, list) and slots:
        out: list[dict[str, str]] = []
        for entry in slots:
            if not isinstance(entry, dict):
                continue
            region_id = (
                entry.get("regionProtocolId")
                or entry.get("regionId")
                or entry.get("regionProtocol")
            )
            if not region_id:
                continue
            slot: dict[str, str] = {"regionProtocolId": str(region_id).strip()}
            label = entry.get("label")
            if label:
                slot["label"] = str(label).strip()
            out.append(slot)
        if out:
            return out

    region_ids = block.get("regionProtocolIds")
    if isinstance(region_ids, list):
        return [
            {"regionProtocolId": str(rid).strip()}
            for rid in region_ids
            if rid is not None and str(rid).strip()
        ]

    return []


def validate_block_protocols(
    block_protocols: list[dict[str, Any]],
    region_protocol_ids: set[str],
) -> list[str]:
    """Return human-readable validation errors (empty if valid)."""
    errors: list[str] = []
    seen_block_ids: set[str] = set()

    for block in block_protocols:
        block_id = str(block.get("id") or "").strip()
        block_name = str(block.get("name") or block_id or "unnamed block")

        if not block_id:
            errors.append(f"Block protocol missing id ({block_name})")
            continue
        if block_id in seen_block_ids:
            errors.append(f"Duplicate block protocol id: {block_id}")
        seen_block_ids.add(block_id)

        slots = normalize_block_slots(block)
        if not slots:
            errors.append(f"Block {block_id} must include at least one region (slots)")
            continue

        slot_ids: list[str] = []
        for index, slot in enumerate(slots, start=1):
            region_id = slot.get("regionProtocolId", "")
            if region_id not in region_protocol_ids:
                errors.append(
                    f"Block {block_id} slot {index}: unknown regionProtocolId {region_id!r}"
                )
            slot_ids.append(region_id)

        if len(slot_ids) != len(set(slot_ids)):
            errors.append(
                f"Block {block_id} lists the same region protocol more than once"
            )

    return errors
