"""Filename template helpers for fetch downloads."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path

from mediatools.core.errors import MediaToolsError

AUTO_FILENAME_LANGUAGE = "auto"
AUTO_FILENAME_LANGUAGE_PLACEHOLDER = "AUTO"
DEFAULT_FILENAME_TEMPLATE = "{lang}-{author}-{title}-{platform}.{ext}"
SAFE_TEMPLATE_RE = re.compile(r"[^A-Za-z0-9._%()/-]+")
TOKEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
LANGUAGE_RE = re.compile(r"^[A-Za-z0-9_-]+$")
LITERAL_EXTENSION_RE = re.compile(r"\.[A-Za-z0-9]{2,5}$")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")

#: Subtitle file extensions that yt-dlp may write.
SUBTITLE_EXTS = {".vtt", ".srt", ".ass", ".ssa", ".lrc"}
#: Regex to match a subtitle filename with a language middle segment.
SUBTITLE_LANG_RE = re.compile(r"^(.+)\.([A-Za-z0-9_-]+)\.(vtt|srt|ass|ssa|lrc)$")

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

logger = logging.getLogger(__name__)

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
    _validate_template_path(template)
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


def _validate_template_path(template: str) -> None:
    normalized = template.strip().replace("\\", "/")
    if normalized.startswith(("/", "~")) or WINDOWS_ABSOLUTE_RE.match(normalized):
        raise MediaToolsError("Output template must be relative to the output directory.")
    if any(part == ".." for part in normalized.split("/")):
        raise MediaToolsError("Output template must not contain '..' path segments.")


def _normalize_language(language: str | None) -> str:
    if language is None:
        raise MediaToolsError("Use --name-language when --name-template contains {lang}.")
    if language.lower() == AUTO_FILENAME_LANGUAGE:
        return AUTO_FILENAME_LANGUAGE_PLACEHOLDER
    normalized = language.strip().upper()
    if not normalized or not LANGUAGE_RE.fullmatch(normalized):
        raise MediaToolsError("Filename language may only contain letters, numbers, '-' or '_'.")
    return normalized

def strip_subtitle_language_suffix(
    output_dir: str | Path,
    *,
    candidates: Iterable[str | Path] | None = None,
) -> None:
    """Remove subtitle language suffixes only when doing so is unambiguous.

    yt-dlp writes subtitle files as <video-base>.<lang>.<fmt> (e.g.
    KR-Title-youtube.en.vtt), but playback tools expect
    <video-base>.srt without a language middle segment for single-language
    subtitles.

    Single-language output is renamed::

        KR-Title-youtube.en.vtt  ->  KR-Title-youtube.vtt

    When multiple languages would collapse to the same target name, all files
    keep their language suffix to avoid data loss.
    """
    dir_path = Path(output_dir)
    if not dir_path.is_dir():
        return

    subs: dict[str, list[Path]] = {}
    for child in _candidate_paths(dir_path, candidates):
        m = SUBTITLE_LANG_RE.match(child.name)
        if m and child.suffix.lower() in SUBTITLE_EXTS:
            base, _lang, sub_ext = m.group(1, 2, 3)
            target_name = f"{base}.{sub_ext}"
            subs.setdefault(target_name, []).append(child)

    for target_name, sources in subs.items():
        if len(sources) > 1:
            logger.warning(
                "Keeping language suffixes for %s because multiple subtitles would collide.",
                target_name,
            )
            continue
        src = sources[0]
        dest = dir_path / target_name
        if dest == src:
            continue
        if dest.exists():
            if _same_file_content(src, dest):
                try:
                    src.unlink()
                    logger.debug(
                        "Removed duplicate subtitle %s; %s already exists.",
                        src.name,
                        dest.name,
                    )
                except OSError:
                    logger.warning(
                        "Keeping duplicate subtitle %s because it could not be removed.",
                        src.name,
                    )
                continue
            logger.warning("Keeping subtitle %s because %s already exists.", src.name, dest.name)
            continue
        src.rename(dest)
        logger.debug("Renamed subtitle %s -> %s", src.name, dest.name)


def prune_original_subtitle_fallbacks(
    output_dir: str | Path,
    *,
    candidates: Iterable[str | Path],
) -> tuple[Path, ...]:
    """Keep the best ``*-orig`` subtitle when original-language fallbacks collide.

    ``--sub-langs original`` expands to a small fallback list such as
    ``pt-BR-orig,pt-BR,pt-orig,pt``.  YouTube may return multiple matches,
    which is useful for fallback but noisy for users.  Prefer the most
    specific ``*-orig`` file and delete the other fallback subtitles for the
    same target name before the language suffix is stripped.
    """
    dir_path = Path(output_dir)
    groups: dict[str, list[tuple[Path, str]]] = {}
    remaining: dict[Path, None] = {}
    for child in _candidate_paths(dir_path, candidates):
        remaining[child] = None
        match = SUBTITLE_LANG_RE.match(child.name)
        if not match or child.suffix.lower() not in SUBTITLE_EXTS:
            continue
        base, language, sub_ext = match.group(1, 2, 3)
        groups.setdefault(f"{base}.{sub_ext}", []).append((child, language))

    for target_name, entries in groups.items():
        originals = [(path, lang) for path, lang in entries if lang.endswith("-orig")]
        if not originals:
            continue
        keep, keep_lang = max(originals, key=lambda item: _language_specificity(item[1]))
        for path, _language in entries:
            if path == keep:
                continue
            try:
                path.unlink()
                remaining.pop(path, None)
                logger.debug(
                    "Removed subtitle fallback %s for original language %s -> %s.",
                    path.name,
                    keep_lang,
                    target_name,
                )
            except OSError:
                logger.warning(
                    "Keeping subtitle fallback %s because it could not be removed.",
                    path.name,
                )

    return tuple(remaining)


def _candidate_paths(
    dir_path: Path,
    candidates: Iterable[str | Path] | None,
) -> list[Path]:
    children = (
        (Path(candidate) for candidate in candidates)
        if candidates is not None
        else dir_path.iterdir()
    )
    result: list[Path] = []
    for child in children:
        if not child.is_absolute():
            child = dir_path / child
        try:
            child.relative_to(dir_path)
        except ValueError:
            logger.warning("Skipping subtitle outside output directory: %s", child)
            continue
        result.append(child)
    return sorted(result)


def _language_specificity(language: str) -> tuple[int, int, str]:
    base = language.removesuffix("-orig")
    return (1 if language.endswith("-orig") else 0, base.count("-"), base)


def _same_file_content(left: Path, right: Path) -> bool:
    try:
        return left.read_bytes() == right.read_bytes()
    except OSError:
        return False

