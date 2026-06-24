"""External media tool helpers.

This module centralizes subprocess calls for ffmpeg-family tools and other
media CLIs used by MediaTools. Callers provide argument lists only; shell
execution is intentionally unsupported.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from mediatools.core.errors import ExternalToolError


@dataclass(frozen=True)
class ToolResult:
    """Completed external tool invocation."""

    command: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]


def find_tool(tool: str) -> str:
    """Return the executable path for *tool* or raise a readable error."""
    executable = shutil.which(tool)
    if executable is None:
        raise ExternalToolError(
            f"{tool} was not found on PATH. Install it and try again.",
            tool=tool,
        )
    return executable


def run_tool(
    tool: str,
    args: Sequence[str],
    *,
    timeout: float | None = 300,
    runner: ProcessRunner = subprocess.run,
) -> ToolResult:
    """Run an external media tool with argument-list invocation."""
    executable = find_tool(tool)
    command = [executable, *args]

    try:
        completed = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExternalToolError(
            f"{tool} timed out after {timeout} seconds.",
            tool=tool,
            details={"command": command, "timeout": timeout},
        ) from exc

    result = ToolResult(
        command=tuple(command),
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        returncode=completed.returncode,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"{tool} failed."
        raise ExternalToolError(
            message,
            tool=tool,
            returncode=result.returncode,
            details={"command": command, "stderr": result.stderr, "stdout": result.stdout},
        )
    return result


def run_ffmpeg(
    args: Sequence[str],
    *,
    timeout: float | None = 300,
    runner: ProcessRunner = subprocess.run,
) -> ToolResult:
    """Run ``ffmpeg`` with safe subprocess defaults."""
    return run_tool("ffmpeg", args, timeout=timeout, runner=runner)


def run_ffprobe(
    args: Sequence[str],
    *,
    timeout: float | None = 60,
    runner: ProcessRunner = subprocess.run,
) -> ToolResult:
    """Run ``ffprobe`` with safe subprocess defaults."""
    return run_tool("ffprobe", args, timeout=timeout, runner=runner)


def run_ytdlp(
    args: Sequence[str],
    *,
    timeout: float | None = None,
    runner: ProcessRunner = subprocess.run,
) -> ToolResult:
    """Run ``yt-dlp`` with safe subprocess defaults."""
    return run_tool("yt-dlp", args, timeout=timeout, runner=runner)
