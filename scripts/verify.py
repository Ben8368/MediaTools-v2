#!/usr/bin/env python3
"""Run the standard MediaTools verification suite.

Used by AI agents, local developers, and CI. Objective checks only;
subjective UX review stays with the user.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_PYTHON_FILE_LINES = 500
LINE_CHECK_DIRS = ("src", "tests", "scripts")


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def step(title: str, command: list[str]) -> None:
    print(f"\n==> {title}")
    print(f"    {' '.join(command)}")
    result = run(command)
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def check_python_file_sizes() -> None:
    """Fail verification if a Python file exceeds the project hard limit."""
    print("\n==> Check Python file sizes")
    oversized: list[tuple[Path, int]] = []
    for directory in LINE_CHECK_DIRS:
        for path in sorted((ROOT / directory).rglob("*.py")):
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) > MAX_PYTHON_FILE_LINES:
                oversized.append((path.relative_to(ROOT), len(lines)))

    if oversized:
        print(f"Python files must not exceed {MAX_PYTHON_FILE_LINES} lines.", file=sys.stderr)
        for path, line_count in oversized:
            print(f"{path}: {line_count} lines", file=sys.stderr)
        raise SystemExit(1)

    print(f"All Python files are <= {MAX_PYTHON_FILE_LINES} lines.")


def report_environment() -> None:
    print("\n==> Environment report")
    version = run([sys.executable, "-m", "mediatools", "--version"])
    print(version.stdout.rstrip() or version.stderr.rstrip())

    doctor = run([sys.executable, "-m", "mediatools", "doctor", "--json"])
    if doctor.returncode != 0:
        print(doctor.stderr.rstrip() or doctor.stdout.rstrip(), file=sys.stderr)
        raise SystemExit(doctor.returncode)

    report = json.loads(doctor.stdout)
    for tool in ("ffmpeg", "ffprobe", "yt-dlp"):
        tool_report = report.get(tool, {})
        if isinstance(tool_report, dict) and tool_report.get("available"):
            print(f"{tool}: found at {tool_report.get('path')}")
        else:
            print(f"{tool}: not found on PATH (informational until that feature is used)")

    console_script = shutil.which("mediatools")
    if console_script:
        print(f"console script: on PATH at {console_script}")
    else:
        print(
            "console script: not on PATH (informational; use `python -m mediatools` instead)",
        )


def main() -> int:
    print(f"MediaTools verify | root={ROOT}")
    check_python_file_sizes()
    step("Install editable package", [sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    step("Run tests", [sys.executable, "-m", "pytest"])
    step("Run ruff", [sys.executable, "-m", "ruff", "check", "."])
    report_environment()
    print("\n==> Verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
