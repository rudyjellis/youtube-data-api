"""thumbnails.set — upload a custom thumbnail."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import Resource
from googleapiclient.http import MediaFileUpload


def set_thumbnail(
    youtube: Resource,
    video_id: str,
    image_path: str | Path,
) -> dict[str, Any]:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Thumbnail not found: {path}")

    suffix = path.suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix, "application/octet-stream")

    media = MediaFileUpload(str(path), mimetype=mime, resumable=True)
    return youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
