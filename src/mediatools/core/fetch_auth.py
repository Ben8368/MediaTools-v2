"""Authentication argument helpers for yt-dlp fetches."""

from __future__ import annotations

from pathlib import Path

from mediatools.core.errors import MediaToolsError
from mediatools.core.paths import normalize


def build_auth_args(
    *,
    cookies: Path | None,
    cookies_from_browser: str | None,
) -> list[str]:
    """Return mutually exclusive yt-dlp cookie arguments."""
    if cookies is not None and cookies_from_browser:
        raise MediaToolsError("Use either --cookies or --cookies-from-browser, not both.")
    if cookies is not None:
        return ["--cookies", str(normalize(cookies))]
    if cookies_from_browser:
        return ["--cookies-from-browser", cookies_from_browser]
    return []


def redact_cookies(args: list[str]) -> list[str]:
    """Return a copy of *args* with ``--cookies`` file paths replaced by ``[REDACTED]``."""
    result: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--cookies" and i + 1 < len(args):
            result.append(args[i])
            result.append("[REDACTED]")
            i += 2
            continue
        result.append(args[i])
        i += 1
    return result
