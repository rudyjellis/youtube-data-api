"""Load brand YAML configs (Doppler secret names only — never values)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from youtube_data_api import DEFAULT_PRIVACY


@dataclass
class BrandSecrets:
    client_id: str
    client_secret: str
    refresh_token: str


@dataclass
class BrandConfig:
    brand_id: str
    display_name: str
    channel_id: str
    gcp_project: str
    oauth_client_type: str
    doppler_project: str
    doppler_config: str
    secrets: BrandSecrets
    defaults: dict[str, Any] = field(default_factory=dict)
    token_cache: str | None = None
    path: Path | None = None

    @property
    def default_privacy(self) -> str:
        return str(self.defaults.get("privacy_status", DEFAULT_PRIVACY)).lower()


def _repo_root() -> Path:
    # src/youtube_data_api/brands.py → repo root is parents[2]
    return Path(__file__).resolve().parents[2]


def brands_dir(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    envish = Path.cwd() / "brands"
    if envish.is_dir():
        return envish
    packaged = _repo_root() / "brands"
    return packaged


def load_brand(brand: str | Path, *, brands_root: Path | None = None) -> BrandConfig:
    """Load a brand by id (e.g. unboundceo) or by path to a YAML file."""
    path = Path(brand)
    if not path.exists():
        root = brands_dir(brands_root)
        candidates = [
            root / f"{brand}.yaml",
            root / f"{brand}.yml",
            root / f"{brand}.brand.yaml",
            root / f"{brand}.brand.yml",
        ]
        path = next((c for c in candidates if c.exists()), candidates[0])
    if not path.is_file():
        raise FileNotFoundError(f"Brand config not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Brand YAML must be a mapping: {path}")

    doppler = raw.get("doppler") or {}
    secrets_raw = raw.get("secrets") or {}
    required_secret_keys = ("client_id", "client_secret", "refresh_token")
    missing = [k for k in required_secret_keys if not secrets_raw.get(k)]
    if missing:
        raise ValueError(f"Brand {path} missing secrets keys: {missing}")

    return BrandConfig(
        brand_id=str(raw.get("brand_id") or path.stem.replace(".brand", "")),
        display_name=str(raw.get("display_name") or raw.get("brand_id") or path.stem),
        channel_id=str(raw["channel_id"]),
        gcp_project=str(raw.get("gcp_project") or "diger-youtube"),
        oauth_client_type=str(raw.get("oauth_client_type") or "desktop"),
        doppler_project=str(doppler.get("project") or "diger-youtube"),
        doppler_config=str(doppler.get("config") or raw.get("brand_id") or "dev"),
        secrets=BrandSecrets(
            client_id=str(secrets_raw["client_id"]),
            client_secret=str(secrets_raw["client_secret"]),
            refresh_token=str(secrets_raw["refresh_token"]),
        ),
        defaults=dict(raw.get("defaults") or {}),
        token_cache=raw.get("token_cache"),
        path=path,
    )


def list_brands(brands_root: Path | None = None) -> list[str]:
    root = brands_dir(brands_root)
    if not root.is_dir():
        return []
    ids: list[str] = []
    for p in sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml")):
        stem = p.name
        if stem.endswith(".brand.yaml"):
            ids.append(stem[: -len(".brand.yaml")])
        elif stem.endswith(".yaml"):
            ids.append(stem[: -len(".yaml")])
        elif stem.endswith(".yml"):
            ids.append(stem[: -len(".yml")])
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out
