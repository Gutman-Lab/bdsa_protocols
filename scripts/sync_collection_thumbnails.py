#!/usr/bin/env python3
"""
Download 2K thumbnails for all large-image items in a BDSA/Girder collection.

Walks the collection folder hierarchy, lists items in each folder, and saves
thumbnails under a local directory that mirrors folder names.

Requires: pip install girder-client  (also listed in backend/requirements.txt)

Usage:
  export BDSA_API_KEY=your_uky_api_key
  python scripts/sync_collection_thumbnails.py

  python scripts/sync_collection_thumbnails.py \\
    --api-url https://bdsa.ai.uky.edu/api/v1 \\
    --collection-id 693c661493ef0d7395814d2f \\
    --output-dir ./thumbnails \\
    --width 2048

  python scripts/sync_collection_thumbnails.py --dry-run
  python scripts/sync_collection_thumbnails.py --force
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterator

from girder_client import GirderClient

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_URL = "https://bdsa.ai.uky.edu/api/v1"
DEFAULT_COLLECTION_ID = "693c661493ef0d7395814d2f"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "thumbnails"
DEFAULT_THUMBNAIL_WIDTH = 2048

_MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

_UNSAFE_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _sanitize_name(name: str) -> str:
    cleaned = _UNSAFE_NAME.sub("_", name.strip())
    return cleaned or "unnamed"


def _authenticate(api_url: str, api_key: str) -> GirderClient:
    gc = GirderClient(apiUrl=api_url)
    gc.authenticate(apiKey=api_key)
    return gc


def _iter_folders(
    gc: GirderClient,
    parent_id: str,
    parent_type: str,
    path_parts: list[str],
) -> Iterator[tuple[str, list[str]]]:
    """Yield (folder_id, relative_path_parts) for every folder under parent."""
    for folder in gc.listFolder(parent_id, parentFolderType=parent_type):
        folder_name = _sanitize_name(folder.get("name") or folder["_id"])
        folder_path = path_parts + [folder_name]
        yield folder["_id"], folder_path
        yield from _iter_folders(gc, folder["_id"], "folder", folder_path)


def _thumbnail_extension(content_type: str | None) -> str:
    if not content_type:
        return ".jpg"
    mime = content_type.split(";", 1)[0].strip().lower()
    return _MIME_EXT.get(mime, ".jpg")


def _thumbnail_dest(
    output_dir: Path,
    folder_path: list[str],
    item: dict[str, Any],
) -> Path:
    item_name = _sanitize_name(item.get("name") or item["_id"])
    stem = f"{item_name}_{item['_id'][:8]}"
    return output_dir.joinpath(*folder_path) / stem


def _download_thumbnail(
    gc: GirderClient,
    item_id: str,
    dest_base: Path,
    width: int,
) -> Path:
    resp = gc.get(
        f"item/{item_id}/tiles/thumbnail",
        parameters={"width": width},
        jsonResp=False,
    )
    ext = _thumbnail_extension(resp.headers.get("Content-Type"))
    dest_path = dest_base.with_suffix(ext)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as handle:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                handle.write(chunk)
    return dest_path


def sync_collection_thumbnails(
    gc: GirderClient,
    collection_id: str,
    output_dir: Path,
    *,
    width: int = DEFAULT_THUMBNAIL_WIDTH,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> dict[str, int]:
    """Walk collection folders and download missing thumbnails."""
    collection = gc.getCollection(collection_id)
    collection_name = _sanitize_name(collection.get("name") or collection_id)
    root_dir = output_dir / collection_name

    stats = {
        "folders": 0,
        "items": 0,
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
    }

    for folder_id, folder_path in _iter_folders(gc, collection_id, "collection", []):
        stats["folders"] += 1
        if verbose:
            print(f"Folder: {'/'.join(folder_path) or '(root)'}")

        for item in gc.listItem(folder_id):
            stats["items"] += 1
            dest_base = _thumbnail_dest(root_dir, folder_path, item)
            existing = sorted(dest_base.parent.glob(f"{dest_base.name}.*"))
            if existing and not force:
                stats["skipped"] += 1
                if verbose:
                    print(f"  skip {item.get('name')} (exists)")
                continue

            if dry_run:
                stats["downloaded"] += 1
                print(f"  would download {item.get('name')} -> {dest_base}.jpg")
                continue

            try:
                dest_path = _download_thumbnail(gc, item["_id"], dest_base, width)
                stats["downloaded"] += 1
                print(f"  saved {item.get('name')} -> {dest_path}")
            except Exception as exc:
                stats["failed"] += 1
                print(f"  failed {item.get('name')} ({item['_id']}): {exc}", file=sys.stderr)

    return stats


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync 2K thumbnails from a BDSA/Girder collection.",
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("BDSA_API_URL", os.environ.get("DSA_API_URL", DEFAULT_API_URL)),
        help=f"Girder API base URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("BDSA_API_KEY", os.environ.get("DSA_API_KEY")),
        help="Girder API key (or set BDSA_API_KEY / DSA_API_KEY)",
    )
    parser.add_argument(
        "--collection-id",
        default=DEFAULT_COLLECTION_ID,
        help=f"Girder collection ID (default: {DEFAULT_COLLECTION_ID})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Local output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_THUMBNAIL_WIDTH,
        help=f"Thumbnail width in pixels (default: {DEFAULT_THUMBNAIL_WIDTH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List downloads without writing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even when a thumbnail file already exists",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every folder and skipped item",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.api_key:
        print(
            "Error: API key required. Pass --api-key or set BDSA_API_KEY / DSA_API_KEY.",
            file=sys.stderr,
        )
        return 1

    gc = _authenticate(args.api_url, args.api_key)
    print(f"Syncing collection {args.collection_id} from {args.api_url}")
    print(f"Thumbnail width: {args.width}px -> {args.output_dir.resolve()}")

    stats = sync_collection_thumbnails(
        gc,
        args.collection_id,
        args.output_dir,
        width=args.width,
        dry_run=args.dry_run,
        force=args.force,
        verbose=args.verbose,
    )

    print(
        f"Done: {stats['folders']} folders, {stats['items']} items, "
        f"{stats['downloaded']} downloaded, {stats['skipped']} skipped, "
        f"{stats['failed']} failed"
    )
    return 1 if stats["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
