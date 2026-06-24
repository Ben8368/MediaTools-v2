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


def test_fetch_dry_run_accepts_friendly_name_template(tmp_path, capsys):
    summary_path = tmp_path / "summary.json"
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
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
            str(tmp_path / "downloads"),
            "--dry-run",
        ],
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "AUTO-%(uploader)s-%(title).200B-%(extractor_key)s.%(ext)s" in output


def test_fetch_dry_run_output_template_overrides_friendly_name(tmp_path, capsys):
    exit_code = main(
        [
            "fetch",
            "https://example.com/video",
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
    exit_code = main(["fetch", "downloads", "--dry-run"])

    assert exit_code == 1
    assert "Provide a fetch URL or --input-file" in capsys.readouterr().err


def test_fetch_dry_run_accepts_input_file(tmp_path, capsys):
    input_file = tmp_path / "urls.txt"
    input_file.write_text("https://example.com/one\nhttps://example.com/two\n", encoding="utf-8")

    exit_code = main(
        [
            "fetch",
            str(tmp_path / "downloads"),
            "--input-file",
            str(input_file),
            "--dry-run",
        ],
    )

    assert exit_code == 0
    assert "Planned 2 item" in capsys.readouterr().out
