#!/usr/bin/env python3
"""Run the standard MediaTools verification suite.

Used by AI agents, local developers, and CI. Objective checks only;
subjective UX review stays with the user.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_SOURCE_FILE_LINES = 500
PYTHON_LINE_CHECK_DIRS = ("src", "tests", "scripts")
FRONTEND_SOURCE_SUFFIXES = {".css", ".ts", ".tsx"}
LEGACY_FRONTEND_OVERSIZED = {
    Path("frontend/src/apps/MediaToolsApps.test.tsx"),
    Path("frontend/src/apps/PhotoshopApp.tsx"),
    Path("frontend/src/styles/mediatools/after-effects.css"),
    Path("frontend/src/styles/mediatools/photoshop.css"),
    Path("frontend/src/styles/mediatools/shared-tools.css"),
}
MIN_PYTHON = (3, 11)
FRONTEND_DIR = ROOT / "frontend"
VERIFY_TMP_DIR = Path(os.environ.get("MEDIATOOLS_VERIFY_TMP", ROOT / ".tmp-verify"))


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _verification_env() -> dict[str, str]:
    """Keep tool caches and user installs inside the workspace."""
    VERIFY_TMP_DIR.mkdir(exist_ok=True)
    temp_dir = VERIFY_TMP_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PIP_CACHE_DIR", str(VERIFY_TMP_DIR / "pip-cache"))
    env.setdefault("PYTHONUSERBASE", str(VERIFY_TMP_DIR / "python-userbase"))
    env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    env.setdefault("npm_config_cache", str(VERIFY_TMP_DIR / "npm-cache"))
    env.setdefault("TEMP", str(temp_dir))
    env.setdefault("TMP", str(temp_dir))
    env.setdefault("TMPDIR", str(temp_dir))
    return env


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_verification_env(),
        errors="replace",
    )


def step(title: str, command: list[str], *, cwd: Path = ROOT) -> None:
    print(f"\n==> {title}")
    print(f"    {' '.join(command)}")
    result = run(command, cwd=cwd)
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        externally_managed = "externally-managed-environment" in result.stderr
        if title == "Install editable package" and externally_managed:
            print(
                "\nThis Python environment is externally managed. On macOS/Homebrew, "
                "create and activate a virtual environment before running verify.py.",
                file=sys.stderr,
            )
        raise SystemExit(result.returncode)


def check_python_version() -> None:
    """Fail early when the interpreter cannot run the project."""
    print("\n==> Check Python version")
    current = sys.version_info
    required = ".".join(str(part) for part in MIN_PYTHON)
    detected = f"{current.major}.{current.minor}.{current.micro}"
    if current < MIN_PYTHON:
        print(
            f"Python {required}+ is required, but this interpreter is {detected}: "
            f"{sys.executable}",
            file=sys.stderr,
        )
        print(
            "On macOS, avoid the Apple Command Line Tools Python 3.9; use a "
            "Homebrew/pyenv Python inside a virtual environment.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(f"Python {detected} OK.")


def check_source_file_sizes() -> None:
    """Fail verification if a non-quarantined source file exceeds the hard limit."""
    print("\n==> Check source file sizes")
    oversized: list[tuple[Path, int]] = []
    quarantined: list[tuple[Path, int]] = []
    for directory in PYTHON_LINE_CHECK_DIRS:
        for path in sorted((ROOT / directory).rglob("*.py")):
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) > MAX_SOURCE_FILE_LINES:
                oversized.append((path.relative_to(ROOT), len(lines)))

    if FRONTEND_DIR.exists():
        for path in sorted((FRONTEND_DIR / "src").rglob("*")):
            if path.suffix not in FRONTEND_SOURCE_SUFFIXES:
                continue
            relative = path.relative_to(ROOT)
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) <= MAX_SOURCE_FILE_LINES:
                continue
            if relative in LEGACY_FRONTEND_OVERSIZED:
                quarantined.append((relative, len(lines)))
                continue
            oversized.append((relative, len(lines)))

    if oversized:
        print(
            f"Source files must not exceed {MAX_SOURCE_FILE_LINES} lines.",
            file=sys.stderr,
        )
        for path, line_count in oversized:
            print(f"{path}: {line_count} lines", file=sys.stderr)
        raise SystemExit(1)

    print(f"All checked source files are <= {MAX_SOURCE_FILE_LINES} lines.")
    if quarantined:
        print("Legacy frontend oversized files are quarantined:")
        for path, line_count in quarantined:
            print(f"- {path}: {line_count} lines")


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


def verify_frontend() -> None:
    """Run the frontend verification suite when the light frontend exists."""
    package_json = FRONTEND_DIR / "package.json"
    package_lock = FRONTEND_DIR / "package-lock.json"
    if not package_json.exists():
        return

    npm = shutil.which("npm")
    if not npm:
        print("npm is required because frontend/package.json exists.", file=sys.stderr)
        raise SystemExit(1)

    if package_lock.exists():
        step("Install frontend dependencies", [npm, "ci"], cwd=FRONTEND_DIR)
    else:
        step("Install frontend dependencies", [npm, "install"], cwd=FRONTEND_DIR)
    step("Run frontend tests", [npm, "run", "test"], cwd=FRONTEND_DIR)
    step("Build frontend", [npm, "run", "build"], cwd=FRONTEND_DIR)


def main() -> int:
    print(f"MediaTools verify | root={ROOT}")
    check_python_version()
    check_source_file_sizes()
    step("Install editable package", [sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    step(
        "Run tests",
        [
            sys.executable,
            "-m",
            "pytest",
            f"--basetemp={VERIFY_TMP_DIR / 'pytest-temp'}",
            "-o",
            f"cache_dir={VERIFY_TMP_DIR / 'pytest-cache'}",
        ],
    )
    step("Run ruff", [sys.executable, "-m", "ruff", "check", "."])
    verify_frontend()
    report_environment()
    print("\n==> Verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
