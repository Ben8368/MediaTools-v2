"""Tests for the post-download transcode logic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mediatools.core.fetch_transcode import (
    _build_transcode_args,
    _codecs_match,
    needs_transcode,
    normalize_codec,
    transcode_if_needed,
)
from mediatools.core.fetch_types import FetchOptions


# ---------------------------------------------------------------------------
# normalize_codec
# ---------------------------------------------------------------------------


class TestNormalizeCodec:
    def test_friendly_video_names(self):
        assert normalize_codec("h264") == "libx264"
        assert normalize_codec("avc") == "libx264"
        assert normalize_codec("h265") == "libx265"
        assert normalize_codec("hevc") == "libx265"
        assert normalize_codec("av1") == "libsvtav1"
        assert normalize_codec("vp9") == "libvpx-vp9"
        assert normalize_codec("vp8") == "libvpx"

    def test_friendly_audio_names(self):
        assert normalize_codec("aac") == "aac"
        assert normalize_codec("opus") == "libopus"
        assert normalize_codec("mp3") == "libmp3lame"
        assert normalize_codec("flac") == "flac"
        assert normalize_codec("vorbis") == "libvorbis"
        assert normalize_codec("ac3") == "ac3"

    def test_known_encoder_passthrough(self):
        assert normalize_codec("libx264") == "libx264"
        assert normalize_codec("libx265") == "libx265"
        assert normalize_codec("libsvtav1") == "libsvtav1"
        assert normalize_codec("copy") == "copy"
        assert normalize_codec("none") == "none"

    def test_unknown_name_passthrough(self):
        assert normalize_codec("some_custom_encoder") == "some_custom_encoder"

    def test_case_insensitive(self):
        assert normalize_codec("H264") == "libx264"
        assert normalize_codec("AAC") == "aac"
        assert normalize_codec("LibX264") == "libx264"

    def test_none_returns_none(self):
        assert normalize_codec(None) is None

    def test_empty_returns_none(self):
        assert normalize_codec("") is None

    def test_whitespace_stripped(self):
        assert normalize_codec("  h264  ") == "libx264"


# ---------------------------------------------------------------------------
# _codecs_match
# ---------------------------------------------------------------------------


class TestCodecsMatch:
    def test_none_target_always_matches(self):
        assert _codecs_match(None, "h264") is True
        assert _codecs_match(None, "vp9") is True
        assert _codecs_match(None, "") is True

    def test_same_codec_matches(self):
        assert _codecs_match("h264", "h264") is True
        assert _codecs_match("aac", "aac") is True

    def test_alias_matches(self):
        # h264 family
        assert _codecs_match("h264", "avc1") is True
        assert _codecs_match("h264", "libx264") is True
        assert _codecs_match("libx264", "h264") is True
        assert _codecs_match("libx264", "avc1") is True
        # hevc family
        assert _codecs_match("h265", "hevc") is True
        assert _codecs_match("hevc", "hev1") is True
        assert _codecs_match("libx265", "hvc1") is True
        # vp9 family
        assert _codecs_match("vp9", "vp9") is True
        assert _codecs_match("libvpx-vp9", "v_vp9") is True
        # aac family
        assert _codecs_match("aac", "mp4a") is True

    def test_different_codecs_dont_match(self):
        assert _codecs_match("h264", "vp9") is False
        assert _codecs_match("h264", "hevc") is False
        assert _codecs_match("aac", "opus") is False
        assert _codecs_match("h265", "av1") is False


# ---------------------------------------------------------------------------
# needs_transcode
# ---------------------------------------------------------------------------


class TestNeedsTranscode:
    def test_no_transcode_options(self):
        opts = FetchOptions(url="https://example.com/v", output_dir=Path("/tmp"))
        assert needs_transcode(opts) is False

    def test_video_codec_set(self):
        opts = FetchOptions(url="https://example.com/v", output_dir=Path("/tmp"), video_codec="h264")
        assert needs_transcode(opts) is True

    def test_audio_codec_set(self):
        opts = FetchOptions(url="https://example.com/v", output_dir=Path("/tmp"), audio_codec="aac")
        assert needs_transcode(opts) is True

    def test_video_bitrate_set(self):
        opts = FetchOptions(url="https://example.com/v", output_dir=Path("/tmp"), video_bitrate="5M")
        assert needs_transcode(opts) is True

    def test_audio_bitrate_set(self):
        opts = FetchOptions(url="https://example.com/v", output_dir=Path("/tmp"), audio_bitrate="128k")
        assert needs_transcode(opts) is True


# ---------------------------------------------------------------------------
# _build_transcode_args
# ---------------------------------------------------------------------------


class TestBuildTranscodeArgs:
    def test_video_transcode_with_crf(self):
        args = _build_transcode_args(
            Path("/input.mp4"),
            Path("/output.mp4"),
            video_codec="h264",
            audio_codec=None,
            video_bitrate=None,
            audio_bitrate=None,
            probed_video_codec="vp9",
            probed_audio_codec="aac",
            overwrite=True,
        )
        assert "-y" in args
        assert "-c:v" in args
        assert "libx264" in args
        assert "-crf" in args
        assert "18" in args
        assert "-movflags" in args
        assert "+faststart" in args

    def test_video_copy_when_matching(self):
        args = _build_transcode_args(
            Path("/input.mp4"),
            Path("/output.mp4"),
            video_codec="h264",
            audio_codec=None,
            video_bitrate=None,
            audio_bitrate=None,
            probed_video_codec="h264",
            probed_audio_codec="aac",
            overwrite=True,
        )
        assert "-c:v" in args
        assert "copy" in args
        assert "-crf" not in args

    def test_audio_transcode_when_mismatch(self):
        args = _build_transcode_args(
            Path("/input.mp4"),
            Path("/output.mp4"),
            video_codec=None,
            audio_codec="aac",
            video_bitrate=None,
            audio_bitrate=None,
            probed_video_codec="h264",
            probed_audio_codec="opus",
            overwrite=True,
        )
        assert "-c:a" in args
        assert "aac" in args
        assert "-b:a" in args
        assert "128k" in args

    def test_audio_copy_when_matching(self):
        args = _build_transcode_args(
            Path("/input.mp4"),
            Path("/output.mp4"),
            video_codec=None,
            audio_codec="aac",
            video_bitrate=None,
            audio_bitrate=None,
            probed_video_codec="h264",
            probed_audio_codec="aac",
            overwrite=True,
        )
        assert "-c:a" in args
        assert "copy" in args

    def test_bitrate_overrides_crf(self):
        args = _build_transcode_args(
            Path("/input.mp4"),
            Path("/output.mp4"),
            video_codec="h264",
            audio_codec=None,
            video_bitrate="5M",
            audio_bitrate=None,
            probed_video_codec="vp9",
            probed_audio_codec="aac",
            overwrite=True,
        )
        assert "-b:v" in args
        assert "5M" in args
        # When bitrate is set, no CRF even if codec mismatches.
        assert "-crf" not in args

    def test_no_overwrite_flag(self):
        args = _build_transcode_args(
            Path("/input.mp4"),
            Path("/output.mp4"),
            video_codec="h264",
            audio_codec=None,
            video_bitrate=None,
            audio_bitrate=None,
            probed_video_codec="vp9",
            probed_audio_codec="aac",
            overwrite=False,
        )
        assert "-n" in args
        assert "-y" not in args

    def test_no_faststart_for_non_mp4(self):
        args = _build_transcode_args(
            Path("/input.mkv"),
            Path("/output.mkv"),
            video_codec="h264",
            audio_codec=None,
            video_bitrate=None,
            audio_bitrate=None,
            probed_video_codec="vp9",
            probed_audio_codec="aac",
            overwrite=True,
        )
        assert "+faststart" not in args


# ---------------------------------------------------------------------------
# transcode_if_needed
# ---------------------------------------------------------------------------


class TestTranscodeIfNeeded:
    def test_returns_none_when_no_transcode_options(self, tmp_path):
        media = tmp_path / "video.mp4"
        media.write_bytes(b"fake")
        opts = FetchOptions(url="https://example.com/v", output_dir=tmp_path)
        assert transcode_if_needed(media, opts) is None

    def test_returns_none_when_codecs_already_match(self, tmp_path):
        """When probing returns matching codecs, no transcode should happen."""
        media = tmp_path / "video.mp4"
        media.write_bytes(b"fake")

        opts = FetchOptions(
            url="https://example.com/v",
            output_dir=tmp_path,
            video_codec="h264",
            audio_codec="aac",
        )

        # Mock probe to return matching codecs.
        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.stdout = '{"streams": [{"codec_type": "video", "codec_name": "h264"}, {"codec_type": "audio", "codec_name": "aac"}], "format": {}}'
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_runner.return_value = mock_result

        result = transcode_if_needed(media, opts, runner=mock_runner)
        assert result is None

    def test_raises_when_file_not_found(self, tmp_path):
        missing = tmp_path / "missing.mp4"
        opts = FetchOptions(
            url="https://example.com/v",
            output_dir=tmp_path,
            video_codec="h264",
        )
        with pytest.raises(Exception):
            transcode_if_needed(missing, opts)
