# youtube-data-api

Reusable **multi-brand** YouTube Data API kit: Desktop OAuth, list uploads, **insert as Unlisted**, update metadata, set thumbnails.

First instance: **Unbound CEO** (`UCwt4BI86Ovzi0eUtv0cs--w`).

## Safety

**Never auto-Public.** Uploads and brand defaults use **Unlisted**. Promoting to `public` requires an explicit `--allow-public` flag (library: `allow_public=True`).

## Layout

```
brands/                 # per-channel YAML (Doppler secret *names* only)
docs/setup-oauth.md     # diger-youtube Desktop client + ops@ test user
src/youtube_data_api/   # auth, list, upload, metadata, thumbnails, CLI
```

## Install

```bash
pip install -e .
youtube-data-api --help
```

Requires Python 3.10+, Doppler CLI (or env vars matching the secret names), and OAuth setup per [docs/setup-oauth.md](docs/setup-oauth.md).

## Brands

| Brand | Channel | Doppler |
| --- | --- | --- |
| `unboundceo` | `UCwt4BI86Ovzi0eUtv0cs--w` | project `youtube-data-api` / config `prd` |
| `example` | placeholder | copy for new channels |

Secret **names** in YAML:

- `YOUTUBE_OAUTH_CLIENT_ID`
- `YOUTUBE_OAUTH_CLIENT_SECRET`
- `YOUTUBE_OAUTH_REFRESH_TOKEN`

Never commit secret values, `client_secret*.json`, or `tokens/`.

## CLI

```bash
youtube-data-api --help
youtube-data-api brands
youtube-data-api --brand unboundceo auth-login
youtube-data-api --brand unboundceo list --max-results 10
youtube-data-api --brand unboundceo upload ./clip.mp4 --title "Draft" --description "..."
youtube-data-api --brand unboundceo update VIDEO_ID --title "New title"
youtube-data-api --brand unboundceo thumbnail VIDEO_ID ./thumb.jpg
```

Upload/update to Public (explicit only):

```bash
youtube-data-api --brand unboundceo upload ./clip.mp4 --title "Live" --privacy public --allow-public
```

## Library

```python
from youtube_data_api.brands import load_brand
from youtube_data_api.client import build_youtube
from youtube_data_api.upload import insert_video

brand = load_brand("unboundceo")
yt = build_youtube(brand)
resp = insert_video(yt, brand, file_path="clip.mp4", title="Draft")  # Unlisted
```

## OAuth

GCP project **`diger-youtube`**, **Desktop** OAuth client, consent-screen test user **`ops@unboundceo.com`**. Full steps: [docs/setup-oauth.md](docs/setup-oauth.md).
