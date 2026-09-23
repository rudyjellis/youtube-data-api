"""videos.update — snippet / status metadata. Never auto-Public."""

from __future__ import annotations

from typing import Any

from googleapiclient.discovery import Resource

from youtube_data_api.list_videos import get_video
from youtube_data_api.privacy import resolve_privacy


def update_metadata(
    youtube: Resource,
    video_id: str,
    *,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    category_id: str | None = None,
    privacy_status: str | None = None,
    allow_public: bool = False,
    made_for_kids: bool | None = None,
) -> dict[str, Any]:
    """Patch video snippet/status. Omits privacyStatus unless explicitly set.

    If privacy_status is provided, public requires allow_public=True.
    """
    existing = get_video(youtube, video_id)
    snippet = dict(existing.get("snippet") or {})
    status = dict(existing.get("status") or {})

    if title is not None:
        snippet["title"] = title
    if description is not None:
        snippet["description"] = description
    if tags is not None:
        snippet["tags"] = list(tags)
    if category_id is not None:
        snippet["categoryId"] = str(category_id)

    if "title" not in snippet or not snippet["title"]:
        raise ValueError("Video is missing title; cannot update snippet")
    if "categoryId" not in snippet:
        snippet["categoryId"] = "22"

    parts = ["snippet"]
    body: dict[str, Any] = {
        "id": video_id,
        "snippet": {
            "title": snippet["title"],
            "description": snippet.get("description") or "",
            "categoryId": snippet["categoryId"],
            "tags": snippet.get("tags") or [],
        },
    }

    if privacy_status is not None or made_for_kids is not None:
        parts.append("status")
        new_status: dict[str, Any] = {}
        if privacy_status is not None:
            new_status["privacyStatus"] = resolve_privacy(
                privacy_status, allow_public=allow_public
            )
        else:
            new_status["privacyStatus"] = status.get("privacyStatus") or "unlisted"
        if made_for_kids is not None:
            new_status["selfDeclaredMadeForKids"] = bool(made_for_kids)
        elif "selfDeclaredMadeForKids" in status:
            new_status["selfDeclaredMadeForKids"] = status["selfDeclaredMadeForKids"]
        body["status"] = new_status

    return youtube.videos().update(part=",".join(parts), body=body).execute()
