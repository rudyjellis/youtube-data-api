"""Multi-brand YouTube Data API kit.

Safety: uploads and metadata updates never set privacyStatus=public unless
the caller explicitly opts in with allow_public=True (CLI requires --allow-public).
Default privacy is always Unlisted.
"""

from __future__ import annotations

__version__ = "0.1.0"

DEFAULT_PRIVACY = "unlisted"
ALLOWED_PRIVACY = frozenset({"private", "unlisted", "public"})

__all__ = [
    "__version__",
    "DEFAULT_PRIVACY",
    "ALLOWED_PRIVACY",
]
