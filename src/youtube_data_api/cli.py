"""CLI entrypoint: youtube-data-api / python -m youtube_data_api."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from youtube_data_api import __version__
from youtube_data_api.auth import run_auth_login
from youtube_data_api.brands import list_brands, load_brand
from youtube_data_api.client import build_youtube
from youtube_data_api.list_videos import get_video, list_channel_videos
from youtube_data_api.metadata import update_metadata
from youtube_data_api.thumbnails import set_thumbnail
from youtube_data_api.upload import insert_video


def _print_json(data: object) -> None:
    click.echo(json.dumps(data, indent=2, default=str))


@click.group()
@click.version_option(__version__, prog_name="youtube-data-api")
@click.option(
    "--brand",
    "brand_id",
    envvar="YOUTUBE_BRAND",
    default="unboundceo",
    show_default=True,
    help="Brand id under brands/ (or path to YAML).",
)
@click.option(
    "--brands-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
    help="Override brands directory.",
)
@click.pass_context
def main(ctx: click.Context, brand_id: str, brands_dir: Path | None) -> None:
    """Multi-brand YouTube Data API kit (Desktop OAuth + Unlisted by default).

    Never auto-Public: uploads default to Unlisted; setting public requires
    --allow-public on the specific command.
    """
    ctx.ensure_object(dict)
    ctx.obj["brand_id"] = brand_id
    ctx.obj["brands_dir"] = brands_dir


def _brand(ctx: click.Context):
    return load_brand(ctx.obj["brand_id"], brands_root=ctx.obj.get("brands_dir"))


@main.command("brands")
@click.pass_context
def brands_cmd(ctx: click.Context) -> None:
    """List available brand configs."""
    for b in list_brands(ctx.obj.get("brands_dir")):
        click.echo(b)


@main.command("auth-login")
@click.option("--force-consent/--no-force-consent", default=True, show_default=True)
@click.pass_context
def auth_login_cmd(ctx: click.Context, force_consent: bool) -> None:
    """Interactive Desktop OAuth; caches token locally (gitignored)."""
    brand = _brand(ctx)
    path = run_auth_login(brand, force_consent=force_consent)
    click.echo(f"Token cache written: {path}", err=True)


@main.command("list")
@click.option("--max-results", default=25, show_default=True, type=int)
@click.option("--page-token", default=None)
@click.pass_context
def list_cmd(ctx: click.Context, max_results: int, page_token: str | None) -> None:
    """List recent uploads for the brand channel."""
    brand = _brand(ctx)
    yt = build_youtube(brand)
    resp = list_channel_videos(
        yt, brand, max_results=max_results, page_token=page_token
    )
    rows = []
    for item in resp.get("items") or []:
        sn = item.get("snippet") or {}
        st = item.get("status") or {}
        vid = (item.get("contentDetails") or {}).get("videoId") or item.get("id")
        rows.append(
            {
                "videoId": vid,
                "title": sn.get("title"),
                "publishedAt": sn.get("publishedAt"),
                "privacyStatus": st.get("privacyStatus"),
            }
        )
    _print_json(
        {
            "channelId": brand.channel_id,
            "nextPageToken": resp.get("nextPageToken"),
            "items": rows,
        }
    )


@main.command("get")
@click.argument("video_id")
@click.pass_context
def get_cmd(ctx: click.Context, video_id: str) -> None:
    """Fetch one video by id."""
    brand = _brand(ctx)
    yt = build_youtube(brand)
    _print_json(get_video(yt, video_id))


@main.command("upload")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--title", required=True)
@click.option("--description", default="")
@click.option("--tag", "tags", multiple=True)
@click.option("--category-id", default=None)
@click.option(
    "--privacy",
    "privacy_status",
    type=click.Choice(["private", "unlisted", "public"], case_sensitive=False),
    default=None,
    help="Default: brand Unlisted. public requires --allow-public.",
)
@click.option(
    "--allow-public",
    is_flag=True,
    default=False,
    help="Required to set privacy=public. Kit never auto-Public.",
)
@click.pass_context
def upload_cmd(
    ctx: click.Context,
    file_path: Path,
    title: str,
    description: str,
    tags: tuple[str, ...],
    category_id: str | None,
    privacy_status: str | None,
    allow_public: bool,
) -> None:
    """Insert (upload) a video. Defaults to Unlisted."""
    brand = _brand(ctx)
    yt = build_youtube(brand)
    resp = insert_video(
        yt,
        brand,
        file_path=file_path,
        title=title,
        description=description,
        tags=list(tags) or None,
        category_id=category_id,
        privacy_status=privacy_status,
        allow_public=allow_public,
    )
    _print_json(
        {
            "id": resp.get("id"),
            "title": (resp.get("snippet") or {}).get("title"),
            "privacyStatus": (resp.get("status") or {}).get("privacyStatus"),
            "url": f"https://youtu.be/{resp.get('id')}",
        }
    )


@main.command("update")
@click.argument("video_id")
@click.option("--title", default=None)
@click.option("--description", default=None)
@click.option("--tag", "tags", multiple=True)
@click.option("--category-id", default=None)
@click.option(
    "--privacy",
    "privacy_status",
    type=click.Choice(["private", "unlisted", "public"], case_sensitive=False),
    default=None,
)
@click.option("--allow-public", is_flag=True, default=False)
@click.option("--made-for-kids/--not-made-for-kids", default=None)
@click.pass_context
def update_cmd(
    ctx: click.Context,
    video_id: str,
    title: str | None,
    description: str | None,
    tags: tuple[str, ...],
    category_id: str | None,
    privacy_status: str | None,
    allow_public: bool,
    made_for_kids: bool | None,
) -> None:
    """Update video metadata. public privacy requires --allow-public."""
    brand = _brand(ctx)
    yt = build_youtube(brand)
    resp = update_metadata(
        yt,
        video_id,
        title=title,
        description=description,
        tags=list(tags) if tags else None,
        category_id=category_id,
        privacy_status=privacy_status,
        allow_public=allow_public,
        made_for_kids=made_for_kids,
    )
    _print_json(
        {
            "id": resp.get("id"),
            "title": (resp.get("snippet") or {}).get("title"),
            "privacyStatus": (resp.get("status") or {}).get("privacyStatus"),
        }
    )


@main.command("thumbnail")
@click.argument("video_id")
@click.argument("image_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_context
def thumbnail_cmd(ctx: click.Context, video_id: str, image_path: Path) -> None:
    """Set a custom thumbnail on a video."""
    brand = _brand(ctx)
    yt = build_youtube(brand)
    resp = set_thumbnail(yt, video_id, image_path)
    _print_json(resp)


if __name__ == "__main__":
    sys.exit(main())
