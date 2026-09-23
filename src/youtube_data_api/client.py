"""YouTube Data API v3 service factory."""

from __future__ import annotations

from googleapiclient.discovery import Resource, build

from youtube_data_api.auth import get_credentials
from youtube_data_api.brands import BrandConfig


def build_youtube(
    brand: BrandConfig,
    *,
    interactive: bool = False,
) -> Resource:
    creds = get_credentials(brand, interactive=interactive)
    return build("youtube", "v3", credentials=creds, cache_discovery=False)
