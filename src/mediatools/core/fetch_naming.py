"""Filename template helpers for fetch downloads."""

from __future__ import annotations

import re

from mediatools.core.errors import MediaToolsError

AUTO_FILENAME_LANGUAGE = "auto"
AUTO_FILENAME_LANGUAGE_PLACEHOLDER = "AUTO"
DEFAULT_FILENAME_TEMPLATE = "{lang}-{author}-{title}-{platform}.{ext}"
SAFE_TEMPLATE_RE = re.compile(r"[^A-Za-z0-9._%()/-]+")
TOKEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
LANGUAGE_RE = re.compile(r"^[A-Za-z0-9_-]+$")
LITERAL_EXTENSION_RE = re.compile(r"\.[A-Za-z0-9]{2,5}$")

FIELD_MAP = {
    "author": "%(uploader)s",
    "creator": "%(creator)s",
    "channel": "%(channel)s",
    "id": "%(id)s",
    "platform": "%(extractor_key)s",
    "title": "%(title).200B",
    "ext": "%(ext)s",
}
LANGUAGE_FIELDS = {"lang", "language"}
LANGUAGE_CODE_MAP = {
    "ar": "AR",
    "en": "EN",
    "ja": "JP",
    "jp": "JP",
    "ko": "KR",
    "kr": "KR",
    "pt": "PT",
    "zh": "SC",
    "zh-cn": "SC",
    "zh-hans": "SC",
    "zh-sg": "SC",
    "zh-tw": "TC",
    "zh-hant": "TC",
    "zh-hk": "TC",
    "zh-mo": "TC",
}


def build_output_template(
    output_template: str | None,
    *,
    filename_template: str | None = None,
    filename_language: str | None = AUTO_FILENAME_LANGUAGE,
) -> str:
    """Return the yt-dlp output template for a fetch request."""
    if output_template is not None:
        return sanitize_output_template(output_template)
    filename_template = filename_template or DEFAULT_FILENAME_TEMPLATE
    return sanitize_output_template(
        render_filename_template(
            filename_template,
            filename_language=filename_language,
        ),
    )


def render_filename_template(
    template: str,
    *,
    filename_language: str | None = None,
) -> str:
    """Convert a friendly template into a yt-dlp output template."""
    cleaned = _ensure_extension(template.strip())
    seen_language = False

    def replace_token(match: re.Match[str]) -> str:
        nonlocal seen_language
        name = match.group(1).lower()
        if name in LANGUAGE_FIELDS:
            seen_language = True
            return _normalize_language(filename_language)
        if name in FIELD_MAP:
            return FIELD_MAP[name]
        supported = ", ".join(sorted([*FIELD_MAP, *LANGUAGE_FIELDS]))
        raise MediaToolsError(f"Unknown filename template field '{name}'. Supported: {supported}.")

    rendered = TOKEN_RE.sub(replace_token, cleaned)
    if "{" in rendered or "}" in rendered:
        raise MediaToolsError("Filename template contains invalid braces.")
    if not seen_language and filename_language:
        _normalize_language(filename_language)
    return rendered


def sanitize_output_template(template: str) -> str:
    """Remove characters that are invalid or awkward across common filesystems."""
    cleaned = template.replace("\\", "/").replace(":", "_")
    cleaned = SAFE_TEMPLATE_RE.sub("_", cleaned)
    cleaned = cleaned.strip(" /.")
    if not cleaned:
        return "%(title).200B.%(ext)s"
    return cleaned


def template_uses_language(template: str | None) -> bool:
    """Return True when a friendly filename template contains a language token."""
    checked = template or DEFAULT_FILENAME_TEMPLATE
    return any(match.group(1).lower() in LANGUAGE_FIELDS for match in TOKEN_RE.finditer(checked))


def normalize_filename_language(language: str | None) -> str:
    """Return a user-facing filename language code."""
    return _normalize_language(language)


def to_filename_language_code(language: str | None) -> str | None:
    """Map a probed media language to the short filename code used by templates."""
    if language is None:
        return None
    normalized = language.strip().replace("_", "-").lower()
    if not normalized or normalized == "na":
        return None
    if normalized in LANGUAGE_CODE_MAP:
        return LANGUAGE_CODE_MAP[normalized]
    base = normalized.split("-", maxsplit=1)[0]
    if base in LANGUAGE_CODE_MAP:
        return LANGUAGE_CODE_MAP[base]
    return base.upper()


def _ensure_extension(template: str) -> str:
    if "{ext}" in template:
        return template
    leaf = template.rsplit("/", maxsplit=1)[-1]
    if LITERAL_EXTENSION_RE.search(leaf):
        return template
    return f"{template}.{{ext}}"


def _normalize_language(language: str | None) -> str:
    if language is None:
        raise MediaToolsError("Use --name-language when --name-template contains {lang}.")
    if language.lower() == AUTO_FILENAME_LANGUAGE:
        return AUTO_FILENAME_LANGUAGE_PLACEHOLDER
    normalized = language.strip().upper()
    if not normalized or not LANGUAGE_RE.fullmatch(normalized):
        raise MediaToolsError("Filename language may only contain letters, numbers, '-' or '_'.")
    return normalized
