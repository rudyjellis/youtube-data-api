"""List channel videos / search uploads."""

from __future__ import annotations

from typing import Any

from googleapiclient.discovery import Resource

from youtube_data_api.brands import BrandConfig


def get_uploads_playlist_id(youtube: Resource, channel_id: str) -> str:
    resp = (
        youtube.channels()
        .list(part="contentDetails", id=channel_id)
        .execute()
    )
    items = resp.get("items") or []
    if not items:
        raise RuntimeError(f"Channel not found or inaccessible: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def list_channel_videos(
    youtube: Resource,
    brand: BrandConfig,
    *,
    max_results: int = 25,
    page_token: str | None = None,
) -> dict[str, Any]:
    """List recent uploads for the brand channel (via uploads playlist)."""
    uploads_id = get_uploads_playlist_id(youtube, brand.channel_id)
    req: dict[str, Any] = {
        "part": "snippet,contentDetails,status",
        "playlistId": uploads_id,
        "maxResults": min(max(1, max_results), 50),
    }
    if page_token:
        req["pageToken"] = page_token
    return youtube.playlistItems().list(**req).execute()


def get_video(youtube: Resource, video_id: str) -> dict[str, Any]:
    resp = (
        youtube.videos()
        .list(part="snippet,status,contentDetails,statistics", id=video_id)
        .execute()
    )
    items = resp.get("items") or []
    if not items:
        raise RuntimeError(f"Video not found: {video_id}")
    return items[0]
