"""Privacy helpers — never auto-Public."""

from __future__ import annotations

from youtube_data_api import ALLOWED_PRIVACY, DEFAULT_PRIVACY


class PrivacyError(ValueError):
    """Raised when a privacy request would violate kit safety rules."""


def resolve_privacy(
    requested: str | None,
    *,
    allow_public: bool = False,
    default: str = DEFAULT_PRIVACY,
) -> str:
    """Return a safe privacyStatus.

    - Default / missing → Unlisted
    - public requires allow_public=True
    - Never silently upgrades to public
    """
    status = (requested or default or DEFAULT_PRIVACY).strip().lower()
    if status not in ALLOWED_PRIVACY:
        raise PrivacyError(
            f"Invalid privacy_status={status!r}; allowed={sorted(ALLOWED_PRIVACY)}"
        )
    if status == "public" and not allow_public:
        raise PrivacyError(
            "Refusing privacy_status=public without allow_public=True "
            "(pass --allow-public on the CLI). Kit never auto-Public."
        )
    return status
