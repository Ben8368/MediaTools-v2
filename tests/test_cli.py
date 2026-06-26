import json
import subprocess
import sys

from mediatools.cli import build_doctor_report, main


def test_version_output(capsys):
    exit_code = main(["--version"])

    assert exit_code == 0
    assert "MediaTools" in capsys.readouterr().out


def test_doctor_json_output(capsys):
    exit_code = main(["doctor", "--json"])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mediatools_version"]
    assert "ffmpeg" in report
    assert "ffprobe" in report
    assert "yt-dlp" in report


def test_doctor_report_shape():
    report = build_doctor_report()

    assert isinstance(report["python_version"], str)
    assert isinstance(report["ffmpeg"], dict)
    assert "available" in report["ffmpeg"]
    assert isinstance(report["ffprobe"], dict)
    assert isinstance(report["yt-dlp"], dict)


def test_module_execution_version():
    result = subprocess.run(
        [sys.executable, "-m", "mediatools", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "MediaTools" in result.stdout


def test_fetch_dry_run_writes_summary(tmp_path, capsys):
    summary_path = tmp_path / "summary.json"
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--dry-run",
            "--write-auto-subs",
            "--sub-langs",
            "en",
            "--write-info-json",
            "--download-archive",
            str(tmp_path / "archive.txt"),
            "--cookies-from-browser",
            "safari",
            "--summary-json",
            str(summary_path),
        ],
    )

    assert exit_code == 0
    assert "Planned 1 item" in capsys.readouterr().out
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["planned"] == 1
    assert summary["items"][0]["url"] == "https://example.com/video"
    assert "--cookies-from-browser" in summary["items"][0]["command"]
    assert "--windows-filenames" in summary["items"][0]["command"]


def test_fetch_dry_run_accepts_legacy_output_dir_positional(tmp_path, capsys):
    summary_path = tmp_path / "summary.json"
    output_dir = tmp_path / "downloads"
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            str(output_dir),
            "--dry-run",
            "--summary-json",
            str(summary_path),
        ],
    )

    assert exit_code == 0
    assert "Planned 1 item" in capsys.readouterr().out
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["items"][0]["output_dir"] == str(output_dir)


def test_fetch_dry_run_accepts_legacy_input_file_output_dir(tmp_path, capsys):
    input_file = tmp_path / "urls.txt"
    input_file.write_text("https://example.com/one\nhttps://example.com/two\n", encoding="utf-8")
    summary_path = tmp_path / "summary.json"
    output_dir = tmp_path / "downloads"

    exit_code = main(
        [
            "fetch",
            str(output_dir),
            "--input-file",
            str(input_file),
            "--dry-run",
            "--summary-json",
            str(summary_path),
        ],
    )

    assert exit_code == 0
    assert "Planned 2 item" in capsys.readouterr().out
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["items"][0]["output_dir"] == str(output_dir)
    assert summary["items"][1]["output_dir"] == str(output_dir)


def test_fetch_rejects_mixed_output_dir_styles(tmp_path, capsys):
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            str(tmp_path / "legacy-downloads"),
            "--output-dir",
            str(tmp_path / "downloads"),
            "--dry-run",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Use either positional output directory or --output-dir" in captured.err


def test_fetch_input_file_keeps_invalid_url_as_url(tmp_path, capsys):
    input_file = tmp_path / "urls.txt"
    input_file.write_text("https://example.com/one\n", encoding="utf-8")

    exit_code = main(
        [
            "fetch",
            "ftp://example.com/video",
            "--input-file",
            str(input_file),
            "--dry-run",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Fetch URL must be an absolute http or https URL" in captured.err


def test_fetch_dry_run_accepts_friendly_name_template(tmp_path, capsys):
    summary_path = tmp_path / "summary.json"
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--dry-run",
            "--name-template",
            "{lang}-{author}-{title}-{platform}.{ext}",
            "--name-language",
            "KR",
            "--summary-json",
            str(summary_path),
        ],
    )

    assert exit_code == 0
    assert "Planned 1 item" in capsys.readouterr().out
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    command = summary["items"][0]["command"]
    assert "KR-%(uploader)s-%(title).200B-%(extractor_key)s.%(ext)s" in command


def test_fetch_dry_run_uses_default_friendly_name_template(tmp_path, capsys):
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--dry-run",
        ],
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "AUTO-%(uploader)s-%(title).200B-%(extractor_key)s.%(ext)s" in output


def test_fetch_dry_run_uses_default_mp4_preset(tmp_path, capsys):
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--dry-run",
        ],
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert " -t mp4 " in output


def test_fetch_audio_codec_disables_default_mp4_preset(tmp_path, monkeypatch):
    captured: dict[str, object] = {}

    def fake_fetch_many(options, *, dry_run, max_workers, timeout):
        from mediatools.core.fetch_types import FetchBatchResult

        captured["preset"] = options[0].preset
        captured["audio_codec"] = options[0].audio_codec
        return FetchBatchResult(items=())

    monkeypatch.setattr("mediatools.commands.fetch.fetch_many", fake_fetch_many)

    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--audio-codec",
            "aac",
        ],
    )

    assert exit_code == 0
    assert captured == {"preset": None, "audio_codec": "aac"}


def test_fetch_uses_default_timeout(tmp_path, monkeypatch, capsys):
    captured: dict[str, object] = {}

    def fake_fetch_many(options, *, dry_run, max_workers, timeout):
        from mediatools.core.fetch_types import FetchBatchResult

        captured["timeout"] = timeout
        return FetchBatchResult(items=())

    monkeypatch.setattr("mediatools.commands.fetch.fetch_many", fake_fetch_many)

    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
        ],
    )

    assert exit_code == 0
    assert captured["timeout"] == 3600.0
    assert "Fetched 0 item" in capsys.readouterr().out


def test_fetch_timeout_zero_means_no_limit(tmp_path, monkeypatch):
    captured: dict[str, object] = {}

    def fake_fetch_many(options, *, dry_run, max_workers, timeout):
        from mediatools.core.fetch_types import FetchBatchResult

        captured["timeout"] = timeout
        return FetchBatchResult(items=())

    monkeypatch.setattr("mediatools.commands.fetch.fetch_many", fake_fetch_many)

    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--timeout",
            "0",
        ],
    )

    assert exit_code == 0
    assert captured["timeout"] is None


def test_fetch_rejects_non_positive_max_concurrent(tmp_path, capsys):
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--dry-run",
            "--max-concurrent",
            "0",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--max-concurrent must be at least 1" in captured.err
    assert "Traceback" not in captured.err


def test_fetch_dry_run_output_template_overrides_friendly_name(tmp_path, capsys):
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--dry-run",
            "--output-template",
            "%(id)s.%(ext)s",
            "--name-template",
            "{lang}-{title}.{ext}",
        ],
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "%(id)s.%(ext)s" in output
    assert "AUTO-%(title).200B" not in output


def test_fetch_requires_url_or_input_file(capsys):
    exit_code = main(["fetch", "--dry-run"])

    assert exit_code == 1
    assert "Provide a fetch URL or --input-file" in capsys.readouterr().err


def test_subtitle_missing_input_reports_clean_error(tmp_path, capsys):
    exit_code = main(
        [
            "subtitle",
            "convert",
            str(tmp_path / "missing.vtt"),
            str(tmp_path / "target.srt"),
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Input subtitle file does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_fetch_input_file_directory_reports_clean_error(tmp_path, capsys):
    exit_code = main(
        [
            "fetch",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--input-file",
            str(tmp_path),
            "--dry-run",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Fetch input path is not a file" in captured.err
    assert "Traceback" not in captured.err


def test_fetch_summary_json_directory_reports_clean_error(tmp_path, capsys):
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--dry-run",
            "--summary-json",
            str(tmp_path),
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Could not write summary JSON" in captured.err
    assert "Traceback" not in captured.err


def test_fetch_dry_run_accepts_input_file(tmp_path, capsys):
    input_file = tmp_path / "urls.txt"
    input_file.write_text("https://example.com/one\nhttps://example.com/two\n", encoding="utf-8")

    exit_code = main(
        [
            "fetch",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--input-file",
            str(input_file),
            "--dry-run",
        ],
    )

    assert exit_code == 0
    assert "Planned 2 item" in capsys.readouterr().out
