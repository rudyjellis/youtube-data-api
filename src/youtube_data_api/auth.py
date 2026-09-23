"""Desktop OAuth + Doppler-backed credentials for YouTube Data API v3.

Never logs or writes secret values into the repo. Token caches are gitignored.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from youtube_data_api.brands import BrandConfig

# Upload + manage requires youtube (not youtube.readonly).
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


class AuthError(RuntimeError):
    """OAuth / credential resolution failure."""


def _doppler_get(project: str, config: str, name: str) -> str:
    """Fetch a single secret value via Doppler CLI (not committed)."""
    env_fallback = os.environ.get(name)
    if env_fallback:
        return env_fallback

    cmd = [
        "doppler",
        "secrets",
        "get",
        name,
        "--project",
        project,
        "--config",
        config,
        "--plain",
    ]
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise AuthError(
            f"Doppler CLI not found and env {name} unset. "
            "Install doppler or export the secret name as an env var."
        ) from exc
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or "").strip()
        raise AuthError(
            f"Failed to read Doppler secret {name!r} "
            f"(project={project} config={config}): {err}"
        ) from exc
    value = (proc.stdout or "").strip()
    if not value:
        raise AuthError(f"Doppler secret {name!r} is empty")
    return value


def resolve_oauth_client(brand: BrandConfig) -> dict[str, Any]:
    """Build an InstalledApp / Desktop client_config dict from Doppler names."""
    client_id = _doppler_get(
        brand.doppler_project, brand.doppler_config, brand.secrets.client_id
    )
    client_secret = _doppler_get(
        brand.doppler_project, brand.doppler_config, brand.secrets.client_secret
    )
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def _token_path(brand: BrandConfig, explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    if brand.token_cache:
        return Path(brand.token_cache)
    return Path("tokens") / f"{brand.brand_id}.token.json"


def _credentials_from_refresh(brand: BrandConfig, client_config: dict[str, Any]) -> Credentials:
    refresh = _doppler_get(
        brand.doppler_project, brand.doppler_config, brand.secrets.refresh_token
    )
    installed = client_config["installed"]
    return Credentials(
        token=None,
        refresh_token=refresh,
        token_uri=installed["token_uri"],
        client_id=installed["client_id"],
        client_secret=installed["client_secret"],
        scopes=SCOPES,
    )


def _load_cached(path: Path) -> Credentials | None:
    if not path.is_file():
        return None
    try:
        return Credentials.from_authorized_user_file(str(path), SCOPES)
    except Exception:
        return None


def _save_cached(creds: Credentials, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def get_credentials(
    brand: BrandConfig,
    *,
    token_path: Path | None = None,
    interactive: bool = False,
    force_consent: bool = False,
) -> Credentials:
    """Return usable Credentials for the brand.

    Order:
    1. Local token cache (gitignored)
    2. Doppler refresh token + client id/secret
    3. Interactive Desktop OAuth (only if interactive=True)
    """
    cache = _token_path(brand, token_path)
    client_config = resolve_oauth_client(brand)

    creds = _load_cached(cache)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_cached(creds, cache)
        return creds

    # Prefer Doppler refresh token (non-interactive CI / agents)
    try:
        creds = _credentials_from_refresh(brand, client_config)
        if not creds.valid:
            creds.refresh(Request())
        _save_cached(creds, cache)
        return creds
    except AuthError:
        if not interactive:
            raise

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    kwargs: dict[str, Any] = {}
    if force_consent:
        kwargs["access_type"] = "offline"
        kwargs["prompt"] = "consent"
    creds = flow.run_local_server(port=0, **kwargs)
    _save_cached(creds, cache)
    return creds


def run_auth_login(brand: BrandConfig, *, force_consent: bool = True) -> Path:
    """Interactive Desktop OAuth; prints where to store the refresh token in Doppler."""
    cache = _token_path(brand)
    creds = get_credentials(
        brand, token_path=cache, interactive=True, force_consent=force_consent
    )
    # Surface refresh token presence without printing the secret value.
    has_refresh = bool(creds.refresh_token)
    meta = {
        "brand_id": brand.brand_id,
        "token_cache": str(cache),
        "has_refresh_token": has_refresh,
        "doppler_secret_name": brand.secrets.refresh_token,
        "doppler_project": brand.doppler_project,
        "doppler_config": brand.doppler_config,
        "note": (
            "Copy the refresh_token from the token cache into Doppler "
            f"as {brand.secrets.refresh_token} (never commit the cache)."
        ),
    }
    print(json.dumps(meta, indent=2))
    return cache
