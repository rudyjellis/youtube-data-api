"""videos.insert — always defaults to Unlisted; never auto-Public."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import Resource
from googleapiclient.http import MediaFileUpload

from youtube_data_api.brands import BrandConfig
from youtube_data_api.privacy import resolve_privacy


def insert_video(
    youtube: Resource,
    brand: BrandConfig,
    *,
    file_path: str | Path,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str | None = None,
    privacy_status: str | None = None,
    allow_public: bool = False,
    made_for_kids: bool | None = None,
    notify_subscribers: bool | None = None,
    chunksize: int = 8 * 1024 * 1024,
) -> dict[str, Any]:
    """Upload a video as Unlisted by default.

    Raises PrivacyError if privacy_status=public without allow_public=True.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")

    privacy = resolve_privacy(
        privacy_status,
        allow_public=allow_public,
        default=brand.default_privacy,
    )
    cat = category_id or str(brand.defaults.get("category_id") or "22")
    kids = (
        brand.defaults.get("made_for_kids", False)
        if made_for_kids is None
        else made_for_kids
    )
    notify = (
        brand.defaults.get("notify_subscribers", False)
        if notify_subscribers is None
        else notify_subscribers
    )

    body: dict[str, Any] = {
        "snippet": {
            "title": title,
            "description": description or "",
            "categoryId": str(cat),
            "channelId": brand.channel_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": bool(kids),
        },
    }
    if tags:
        body["snippet"]["tags"] = list(tags)

    media = MediaFileUpload(
        str(path),
        chunksize=chunksize,
        resumable=True,
        mimetype="application/octet-stream",
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
        notifySubscribers=bool(notify),
    )

    response = None
    while response is None:
        _status, response = request.next_chunk()
    return response
