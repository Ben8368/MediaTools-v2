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
