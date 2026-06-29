"""Runtime resolution helpers for fetch options."""

from __future__ import annotations

import json
import re
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


def probe_original_subtitle_language(
    url: str,
    *,
    cookies: Path | None = None,
    cookies_from_browser: str | None = None,
    runner: ProcessRunner | None = None,
) -> str | None:
    """Return a likely source subtitle language when video language is unavailable."""
    validate_url(url)
    try:
        kwargs = {"runner": runner} if runner is not None else {}
        result = run_ytdlp(
            [
                *build_auth_args(cookies=cookies, cookies_from_browser=cookies_from_browser),
                "--dump-single-json",
                "--skip-download",
                url,
            ],
            timeout=60,
            **kwargs,
        )
    except ExternalToolError:
        return None

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    subtitles = payload.get("subtitles")
    if isinstance(subtitles, dict):
        subtitle_langs = _non_empty_language_keys(subtitles)
        if len(subtitle_langs) == 1:
            return subtitle_langs[0]

    automatic = payload.get("automatic_captions")
    if isinstance(automatic, dict):
        source_langs = [
            lang
            for lang in _non_empty_language_keys(automatic)
            if _has_source_caption_url(automatic[lang])
        ]
        if len(source_langs) == 1:
            return source_langs[0]
    return None


def _non_empty_language_keys(captions: dict[object, object]) -> list[str]:
    return [
        str(lang)
        for lang, formats in captions.items()
        if str(lang).strip() and isinstance(formats, list) and formats
    ]


def _has_source_caption_url(formats: object) -> bool:
    """Return True for YouTube's source auto-caption URL, excluding translations."""
    if not isinstance(formats, list):
        return False
    for item in formats:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", ""))
        if url and "tlang%3D" not in url and "tlang=" not in url:
            return True
    return False


#: yt-dlp sub-langs regex that matches only the original auto-caption track.
#: YouTube tags the source-language auto-caption with an ``-orig`` suffix
#: (e.g. ``en-orig``, ``zh-CN-orig``) regardless of whether ``--print language``
#: succeeds, and translated captions never carry it.  Used as the fallback when
#: language probing returns nothing so "original subtitles" still resolves to a
#: single, correct track instead of being dropped.
ORIGINAL_AUTOCAPTION_FALLBACK = "^.*-orig$"


def resolve_sub_langs(options: FetchOptions, *, probed_lang: str | None) -> FetchOptions:
    """Replace the 'original' magic keyword with a detected language code."""
    if options.subtitle_languages != "original":
        return options
    lang = probed_lang
    if not lang:
        return copy_options(options, subtitle_languages=ORIGINAL_AUTOCAPTION_FALLBACK)
    elif "-" in lang:
        base = lang.split("-")[0]
        resolved = ",".join(
            _exact_sub_lang(item)
            for item in (f"{lang}-orig", lang, f"{base}-orig", base)
        )
    else:
        resolved = ",".join(_exact_sub_lang(item) for item in (f"{lang}-orig", lang))
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


def _exact_sub_lang(language: str) -> str:
    """Return a yt-dlp subtitle-language regex that matches exactly one tag."""
    return f"^{re.escape(language)}$"
