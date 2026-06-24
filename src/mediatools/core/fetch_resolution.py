"""Runtime resolution helpers for fetch options."""

from __future__ import annotations

from pathlib import Path

from mediatools.core.errors import ExternalToolError
from mediatools.core.fetch_auth import build_auth_args
from mediatools.core.fetch_naming import (
    template_uses_language,
    to_filename_language_code,
)
from mediatools.core.fetch_types import FetchOptions, copy_options, validate_url
from mediatools.core.ffmpeg import ProcessRunner, run_ytdlp


def probe_language(
    url: str,
    *,
    cookies: Path | None = None,
    cookies_from_browser: str | None = None,
    runner: ProcessRunner | None = None,
) -> str | None:
    """Return the video's primary language code, or None on failure."""
    validate_url(url)
    try:
        kwargs = {"runner": runner} if runner is not None else {}
        result = run_ytdlp(
            [
                *build_auth_args(cookies=cookies, cookies_from_browser=cookies_from_browser),
                "--print",
                "language",
                "--skip-download",
                url,
            ],
            timeout=60,
            **kwargs,
        )
    except ExternalToolError:
        return None
    for line in result.stdout.splitlines():
        lang = line.strip()
        if lang and lang != "NA":
            return lang
    return None


def resolve_sub_langs(options: FetchOptions, *, probed_lang: str | None) -> FetchOptions:
    """Replace the 'original' magic keyword with a detected language code."""
    if options.subtitle_languages != "original":
        return options
    lang = probed_lang
    if not lang:
        resolved = "all"
    elif "-" in lang:
        base = lang.split("-")[0]
        resolved = f"{lang}-orig,{lang},{base}-orig,{base}"
    else:
        resolved = f"{lang}-orig,{lang}"
    return copy_options(options, subtitle_languages=resolved)


def resolve_filename_language(options: FetchOptions, *, probed_lang: str | None) -> FetchOptions:
    """Replace the automatic filename language marker with a probed short code."""
    if (options.filename_language or "").lower() != "auto":
        return options
    if not template_uses_language(options.filename_template):
        return options
    return copy_options(
        options,
        filename_language=to_filename_language_code(probed_lang) or "UN",
    )
