"""Post-download transcoding for fetch operations.

When the downloaded media codec does not match the user's target codec,
this module transcodes the file using ffmpeg and replaces the original.
"""

from __future__ import annotations

import logging
from pathlib import Path

from mediatools.core.errors import MediaToolsError
from mediatools.core.ffmpeg import ProcessRunner, run_ffmpeg
from mediatools.core.fetch_types import FetchOptions
from mediatools.core.paths import normalize
from mediatools.core.probe import probe_media

logger = logging.getLogger(__name__)

# Friendly codec names → ffmpeg encoder names.
_CODEC_ALIASES: dict[str, str] = {
    # Video
    "h264": "libx264",
    "avc": "libx264",
    "h265": "libx265",
    "hevc": "libx265",
    "av1": "libsvtav1",
    "vp9": "libvpx-vp9",
    "vp8": "libvpx",
    # Audio
    "aac": "aac",
    "opus": "libopus",
    "mp3": "libmp3lame",
    "flac": "flac",
    "vorbis": "libvorbis",
    "ac3": "ac3",
}

# Known ffmpeg encoder names (pass through unchanged).
_KNOWN_ENCODERS: frozenset[str] = frozenset(
    {
        "libx264",
        "libx265",
        "libsvtav1",
        "libaom-av1",
        "librav1e",
        "libvpx",
        "libvpx-vp9",
        "aac",
        "libfdk_aac",
        "libopus",
        "libmp3lame",
        "flac",
        "libvorbis",
        "ac3",
        "copy",
        "none",
    },
)

# Probed codec_name aliases — multiple names for the same codec family.
_CODEC_FAMILY: dict[str, str] = {
    "h264": "h264",
    "avc1": "h264",
    "avc": "h264",
    "h264_cuvid": "h264",
    "libx264": "h264",
    "hevc": "hevc",
    "h265": "hevc",
    "hev1": "hevc",
    "hvc1": "hevc",
    "libx265": "hevc",
    "vp9": "vp9",
    "v_vp9": "vp9",
    "libvpx-vp9": "vp9",
    "av1": "av1",
    "av01": "av1",
    "libsvtav1": "av1",
    "libaom-av1": "av1",
    "aac": "aac",
    "mp4a": "aac",
    "libfdk_aac": "aac",
    "opus": "opus",
    "libopus": "opus",
    "mp3": "mp3",
    "libmp3lame": "mp3",
    "flac": "flac",
    "vorbis": "vorbis",
    "libvorbis": "vorbis",
}


def normalize_codec(name: str | None) -> str | None:
    """Normalize a user-provided codec name to an ffmpeg encoder name.

    Accepts friendly names (``h264``, ``hevc``, ``aac``) or ffmpeg encoder
    names (``libx264``, ``libx265``).  Unknown names pass through unchanged
    so ffmpeg can validate them.
    """
    if not name:
        return None
    lower = name.lower().strip()
    if lower in _KNOWN_ENCODERS:
        return lower
    return _CODEC_ALIASES.get(lower, lower)


def _codecs_match(target: str | None, probed_codec_name: str) -> bool:
    """Return True if *target* codec matches the *probed_codec_name*.

    Compares via codec family aliases so ``h264`` matches ``avc1``,
    ``libx264``, etc.  Returns ``True`` when *target* is ``None`` (no
    constraint).
    """
    if not target:
        return True
    target_family = _CODEC_FAMILY.get(normalize_codec(target) or "", "")
    probed_family = _CODEC_FAMILY.get(probed_codec_name.lower(), probed_codec_name.lower())
    if target_family and probed_family:
        return target_family == probed_family
    # Fallback: direct string match after normalization.
    return (normalize_codec(target) or "").lower() == probed_codec_name.lower()


def needs_transcode(options: FetchOptions) -> bool:
    """Return True if any transcode option is set."""
    return bool(
        options.video_codec
        or options.audio_codec
        or options.video_bitrate
        or options.audio_bitrate
    )


def _build_transcode_args(
    input_path: Path,
    output_path: Path,
    *,
    video_codec: str | None,
    audio_codec: str | None,
    video_bitrate: str | None,
    audio_bitrate: str | None,
    probed_video_codec: str,
    probed_audio_codec: str,
    overwrite: bool,
) -> list[str]:
    """Build ffmpeg arguments for conditional transcoding.

    Uses ``copy`` when the probed codec already matches the target, and
    the user did not explicitly request a bitrate override.
    """
    args = ["-y" if overwrite else "-n", "-i", str(normalize(input_path))]

    # Video codec selection.
    if video_codec:
        normalized = normalize_codec(video_codec)
        if _codecs_match(video_codec, probed_video_codec) and not video_bitrate:
            args.extend(["-c:v", "copy"])
        else:
            args.extend(["-c:v", normalized or video_codec])
            if not video_bitrate:
                args.extend(_default_crf_args(normalized or video_codec))
    if video_bitrate:
        args.extend(["-b:v", video_bitrate])

    # Audio codec selection.
    if audio_codec:
        normalized_a = normalize_codec(audio_codec)
        if _codecs_match(audio_codec, probed_audio_codec) and not audio_bitrate:
            args.extend(["-c:a", "copy"])
        else:
            args.extend(["-c:a", normalized_a or audio_codec])
            if not audio_bitrate:
                args.extend(["-b:a", _default_audio_bitrate(normalized_a or audio_codec)])
    if audio_bitrate:
        args.extend(["-b:a", audio_bitrate])

    # Container optimizations.
    suffix = output_path.suffix.lower()
    if suffix == ".mp4":
        args.extend(["-movflags", "+faststart"])

    args.append(str(normalize(output_path)))
    return args


def _default_crf_args(encoder: str) -> list[str]:
    """Return CRF flags for the given encoder."""
    crf_defaults = {
        "libx264": ["-crf", "18", "-preset", "slow"],
        "libx265": ["-crf", "22", "-preset", "slow"],
        "libsvtav1": ["-crf", "30", "-preset", "6"],
        "libvpx-vp9": ["-crf", "30", "-b:v", "0"],
    }
    return crf_defaults.get(encoder, [])


def _default_audio_bitrate(encoder: str) -> str:
    """Return a sensible default audio bitrate for the encoder."""
    defaults = {
        "aac": "128k",
        "libfdk_aac": "128k",
        "libopus": "128k",
        "libmp3lame": "192k",
        "libvorbis": "128k",
        "ac3": "192k",
        "flac": "0",  # Lossless, bitrate ignored.
    }
    return defaults.get(encoder, "128k")


def _probe_stream_codecs(
    media_path: Path,
    *,
    runner: ProcessRunner | None = None,
) -> tuple[str, str]:
    """Return ``(video_codec_name, audio_codec_name)`` from ffprobe.

    Returns empty strings when the corresponding stream type is not found.
    """
    kwargs = {"runner": runner} if runner is not None else {}
    data = probe_media(media_path, **kwargs)
    streams = data.get("streams", [])
    if not isinstance(streams, list):
        return ("", "")
    video_codec = ""
    audio_codec = ""
    for stream in streams:
        if not isinstance(stream, dict):
            continue
        codec_type = stream.get("codec_type", "")
        codec_name = stream.get("codec_name", "")
        if codec_type == "video" and not video_codec:
            video_codec = str(codec_name)
        elif codec_type == "audio" and not audio_codec:
            audio_codec = str(codec_name)
    return video_codec, audio_codec


def transcode_if_needed(
    download_path: Path,
    options: FetchOptions,
    *,
    runner: ProcessRunner | None = None,
) -> dict[str, object] | None:
    """Transcode *download_path* if its codecs don't match the targets.

    Probes the downloaded file, compares codecs against ``options.video_codec``
    and ``options.audio_codec``, and transcodes only when there is a mismatch.
    The original file is replaced in-place (via temp file swap).

    Returns a dict with transcode info if transcoding happened, or ``None``
    if the file already matched.
    """
    if not needs_transcode(options):
        return None

    path = normalize(download_path)
    if not path.exists():
        raise MediaToolsError(f"Downloaded file not found: {path}")

    probed_v, probed_a = _probe_stream_codecs(path, runner=runner)

    video_match = _codecs_match(options.video_codec, probed_v)
    audio_match = _codecs_match(options.audio_codec, probed_a)

    if video_match and audio_match:
        logger.info("Codecs already match target — skipping transcode.")
        return None

    logger.info(
        "Transcoding needed: video %s→%s, audio %s→%s",
        probed_v,
        options.video_codec or "copy",
        probed_a,
        options.audio_codec or "copy",
    )

    # Transcode to a temp file in the same directory, then swap.
    tmp_path = path.parent / f"{path.stem}.transcoding{path.suffix}"
    try:
        args = _build_transcode_args(
            path,
            tmp_path,
            video_codec=options.video_codec,
            audio_codec=options.audio_codec,
            video_bitrate=options.video_bitrate,
            audio_bitrate=options.audio_bitrate,
            probed_video_codec=probed_v,
            probed_audio_codec=probed_a,
            overwrite=True,
        )
        kwargs = {"runner": runner} if runner is not None else {}
        run_ffmpeg(args, timeout=None, **kwargs)

        # Replace original with transcoded file.
        path.unlink()
        tmp_path.rename(path)

        result_info: dict[str, object] = {
            "transcoded": True,
            "original_video_codec": probed_v,
            "original_audio_codec": probed_a,
            "target_video_codec": options.video_codec,
            "target_audio_codec": options.audio_codec,
        }
        logger.info("Transcode complete: %s", path.name)
        return result_info

    except Exception:
        # Clean up temp file on failure.
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
