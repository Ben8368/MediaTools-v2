"""Best-effort GPU utilization probes for local system metrics."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class GpuMetrics:
    percent: float
    available: bool
    detail: str


def _run_tool(command: list[str]) -> str:
    if not shutil.which(command[0]):
        return ""
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=2.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout


def _read_nvidia_gpu_percent() -> GpuMetrics | None:
    output = _run_tool([
        "nvidia-smi",
        "--query-gpu=utilization.gpu",
        "--format=csv,noheader,nounits",
    ])
    values: list[float] = []
    for line in output.splitlines():
        try:
            values.append(float(line.strip()))
        except ValueError:
            continue
    if not values:
        return None
    return GpuMetrics(
        percent=max(values),
        available=True,
        detail="NVIDIA GPU utilization via nvidia-smi.",
    )


def _read_macos_gpu_percent() -> GpuMetrics | None:
    output = _run_tool(["ioreg", "-r", "-d", "1", "-c", "IOAccelerator"])
    values = [
        float(match.group(1))
        for match in re.finditer(r'"Device Utilization %"\s*=\s*(\d+(?:\.\d+)?)', output)
    ]
    if not values:
        values = [
            float(match.group(1))
            for match in re.finditer(r'"Renderer Utilization %"\s*=\s*(\d+(?:\.\d+)?)', output)
        ]
    if not values:
        return None
    return GpuMetrics(
        percent=max(values),
        available=True,
        detail="macOS GPU utilization via IOAccelerator.",
    )


def read_gpu_metrics() -> GpuMetrics:
    nvidia = _read_nvidia_gpu_percent()
    if nvidia is not None:
        return nvidia
    if platform.system() == "Darwin":
        macos = _read_macos_gpu_percent()
        if macos is not None:
            return macos
    return GpuMetrics(
        percent=0.0,
        available=False,
        detail="当前平台未暴露可读取的 GPU 利用率。",
    )
