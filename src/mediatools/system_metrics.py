"""Best-effort local system metrics for the light frontend."""

from __future__ import annotations

import ctypes
import os
import platform
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from mediatools.system_gpu import read_gpu_metrics


@dataclass(frozen=True)
class _CpuCounters:
    idle: int
    total: int


@dataclass(frozen=True)
class _NetworkCounters:
    received: int
    sent: int


class _Guid(ctypes.Structure):
    _fields_ = [
        ("data1", ctypes.c_ulong),
        ("data2", ctypes.c_ushort),
        ("data3", ctypes.c_ushort),
        ("data4", ctypes.c_ubyte * 8),
    ]


class _MibIfRow2(ctypes.Structure):
    _fields_ = [
        ("interface_luid", ctypes.c_ulonglong),
        ("interface_index", ctypes.c_ulong),
        ("interface_guid", _Guid),
        ("alias", ctypes.c_wchar * 257),
        ("description", ctypes.c_wchar * 257),
        ("physical_address_length", ctypes.c_ulong),
        ("physical_address", ctypes.c_ubyte * 32),
        ("permanent_physical_address", ctypes.c_ubyte * 32),
        ("mtu", ctypes.c_ulong),
        ("interface_type", ctypes.c_ulong),
        ("tunnel_type", ctypes.c_int),
        ("media_type", ctypes.c_int),
        ("physical_medium_type", ctypes.c_int),
        ("access_type", ctypes.c_int),
        ("direction_type", ctypes.c_int),
        ("interface_and_oper_status_flags", ctypes.c_ubyte),
        ("oper_status", ctypes.c_int),
        ("admin_status", ctypes.c_int),
        ("media_connect_state", ctypes.c_int),
        ("network_guid", _Guid),
        ("connection_type", ctypes.c_int),
        ("transmit_link_speed", ctypes.c_ulonglong),
        ("receive_link_speed", ctypes.c_ulonglong),
        ("in_octets", ctypes.c_ulonglong),
        ("in_ucast_pkts", ctypes.c_ulonglong),
        ("in_nucast_pkts", ctypes.c_ulonglong),
        ("in_discards", ctypes.c_ulonglong),
        ("in_errors", ctypes.c_ulonglong),
        ("in_unknown_protos", ctypes.c_ulonglong),
        ("in_ucast_octets", ctypes.c_ulonglong),
        ("in_multicast_octets", ctypes.c_ulonglong),
        ("in_broadcast_octets", ctypes.c_ulonglong),
        ("out_octets", ctypes.c_ulonglong),
        ("out_ucast_pkts", ctypes.c_ulonglong),
        ("out_nucast_pkts", ctypes.c_ulonglong),
        ("out_discards", ctypes.c_ulonglong),
        ("out_errors", ctypes.c_ulonglong),
        ("out_ucast_octets", ctypes.c_ulonglong),
        ("out_multicast_octets", ctypes.c_ulonglong),
        ("out_broadcast_octets", ctypes.c_ulonglong),
        ("out_qlen", ctypes.c_ulonglong),
    ]


def _clamp_percent(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(max(0.0, min(float(value), 100.0)), 1)


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


def _read_linux_cpu_counters() -> _CpuCounters | None:
    stat_path = Path("/proc/stat")
    if not stat_path.exists():
        return None
    first_line = stat_path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    parts = first_line.split()
    if not parts or parts[0] != "cpu":
        return None
    values = [int(value) for value in parts[1:]]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return _CpuCounters(idle=idle, total=sum(values))


def _read_windows_cpu_counters() -> _CpuCounters | None:
    if platform.system() != "Windows":
        return None

    class FileTime(ctypes.Structure):
        _fields_ = [
            ("dwLowDateTime", ctypes.c_ulong),
            ("dwHighDateTime", ctypes.c_ulong),
        ]

        def as_int(self) -> int:
            return (self.dwHighDateTime << 32) + self.dwLowDateTime

    idle_time = FileTime()
    kernel_time = FileTime()
    user_time = FileTime()
    ok = ctypes.windll.kernel32.GetSystemTimes(  # type: ignore[attr-defined]
        ctypes.byref(idle_time),
        ctypes.byref(kernel_time),
        ctypes.byref(user_time),
    )
    if not ok:
        return None
    kernel = kernel_time.as_int()
    user = user_time.as_int()
    return _CpuCounters(idle=idle_time.as_int(), total=kernel + user)


def _read_load_percent() -> float | None:
    try:
        load_1m, _, _ = os.getloadavg()
    except (AttributeError, OSError):
        return None
    cpu_count = os.cpu_count() or 1
    return (load_1m / cpu_count) * 100


def _read_macos_cpu_percent() -> float | None:
    output = _run_tool(["ps", "-A", "-o", "%cpu="])
    values: list[float] = []
    for line in output.splitlines():
        try:
            values.append(float(line.strip()))
        except ValueError:
            continue
    if not values:
        return _read_load_percent()
    return sum(values) / max(os.cpu_count() or 1, 1)


def _cpu_percent_from_delta(
    current: _CpuCounters | None,
    previous: _CpuCounters | None,
) -> float | None:
    if current is None or previous is None:
        return None
    total_delta = current.total - previous.total
    idle_delta = current.idle - previous.idle
    if total_delta <= 0:
        return None
    return (1 - (idle_delta / total_delta)) * 100


def _read_linux_memory_percent() -> float | None:
    meminfo_path = Path("/proc/meminfo")
    if not meminfo_path.exists():
        return None
    values: dict[str, int] = {}
    for line in meminfo_path.read_text(encoding="utf-8", errors="replace").splitlines():
        key, _, rest = line.partition(":")
        amount = rest.strip().split()[0] if rest.strip() else ""
        if amount.isdigit():
            values[key] = int(amount)
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if not total or available is None:
        return None
    return ((total - available) / total) * 100


def _read_macos_memory_percent() -> float | None:
    total_output = _run_tool(["sysctl", "-n", "hw.memsize"]).strip()
    vm_output = _run_tool(["vm_stat"])
    if not total_output.isdigit() or not vm_output:
        return None
    total_bytes = int(total_output)
    page_size_match = re.search(r"page size of (\d+) bytes", vm_output)
    page_size = int(page_size_match.group(1)) if page_size_match else 4096
    page_counts: dict[str, int] = {}
    for line in vm_output.splitlines():
        name, _, value = line.partition(":")
        digits = re.sub(r"[^0-9]", "", value)
        if digits:
            page_counts[name.strip()] = int(digits)
    free_pages = (
        page_counts.get("Pages free", 0)
        + page_counts.get("Pages speculative", 0)
        + page_counts.get("Pages inactive", 0)
    )
    used_bytes = max(0, total_bytes - free_pages * page_size)
    return (used_bytes / total_bytes) * 100 if total_bytes else None


def _read_windows_memory_percent() -> float | None:
    if platform.system() != "Windows":
        return None

    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))  # type: ignore[attr-defined]
    if not ok:
        return None
    return float(status.dwMemoryLoad)


def _read_memory_percent() -> float | None:
    system = platform.system()
    if system == "Darwin":
        return _read_macos_memory_percent()
    if system == "Linux":
        return _read_linux_memory_percent()
    if system == "Windows":
        return _read_windows_memory_percent()
    return None


def _read_linux_network_counters() -> _NetworkCounters | None:
    dev_path = Path("/proc/net/dev")
    if not dev_path.exists():
        return None
    received = 0
    sent = 0
    for line in dev_path.read_text(encoding="utf-8", errors="replace").splitlines()[2:]:
        name, _, rest = line.partition(":")
        if name.strip() == "lo":
            continue
        fields = rest.split()
        if len(fields) >= 16:
            received += int(fields[0])
            sent += int(fields[8])
    return _NetworkCounters(received=received, sent=sent)


def _read_macos_network_counters() -> _NetworkCounters | None:
    output = _run_tool(["netstat", "-ibn"])
    interfaces: dict[str, tuple[int, int]] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 10 or parts[0] == "Name" or parts[0].startswith("lo"):
            continue
        try:
            received = int(parts[6])
            sent = int(parts[9])
        except ValueError:
            continue
        previous = interfaces.get(parts[0], (0, 0))
        interfaces[parts[0]] = (max(previous[0], received), max(previous[1], sent))
    if not interfaces:
        return None
    return _NetworkCounters(
        received=sum(item[0] for item in interfaces.values()),
        sent=sum(item[1] for item in interfaces.values()),
    )


def _read_windows_network_counters() -> _NetworkCounters | None:
    counters = _read_windows_iphlpapi_network_counters()
    if counters is not None:
        return counters
    output = _run_tool(["netstat", "-e"])
    for line in output.splitlines():
        parts = line.split()
        counters = _parse_windows_netstat_counter_line(parts)
        if counters is not None:
            return counters
    return None


def _read_windows_iphlpapi_network_counters() -> _NetworkCounters | None:
    if platform.system() != "Windows":
        return None
    try:
        iphlpapi = ctypes.windll.iphlpapi  # type: ignore[attr-defined]
    except AttributeError:
        return None

    table = ctypes.c_void_p()
    get_table = iphlpapi.GetIfTable2
    get_table.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    get_table.restype = ctypes.c_ulong
    if get_table(ctypes.byref(table)) != 0 or not table.value:
        return None

    free_table = iphlpapi.FreeMibTable
    free_table.argtypes = [ctypes.c_void_p]
    try:
        row_offset = _aligned_table_row_offset()
        count = ctypes.c_ulong.from_address(table.value).value
        rows_address = table.value + row_offset
        rows = [
            _MibIfRow2.from_address(rows_address + index * ctypes.sizeof(_MibIfRow2))
            for index in range(count)
        ]
        active_rows = [
            row
            for row in rows
            if row.oper_status == 1 and row.interface_type != 24
        ]
        selected_rows = active_rows or [row for row in rows if row.interface_type != 24]
        if not selected_rows:
            return None
        return _NetworkCounters(
            received=sum(int(row.in_octets) for row in selected_rows),
            sent=sum(int(row.out_octets) for row in selected_rows),
        )
    finally:
        free_table(table)


def _aligned_table_row_offset() -> int:
    return ((ctypes.sizeof(ctypes.c_ulong) + 7) // 8) * 8


def _parse_windows_netstat_counter_line(parts: list[str]) -> _NetworkCounters | None:
    """Parse the bytes row from ``netstat -e`` across localized Windows output."""
    if len(parts) < 3:
        return None
    label = parts[0].lower()
    if not label.startswith("bytes") and not _looks_like_counter_header(label):
        return None
    numeric_parts = [part for part in parts[1:] if part.isdigit()]
    if len(numeric_parts) < 2:
        return None
    try:
        return _NetworkCounters(received=int(numeric_parts[0]), sent=int(numeric_parts[1]))
    except ValueError:
        return None


def _looks_like_counter_header(label: str) -> bool:
    """Return True for localized byte labels while avoiding packet/error rows."""
    packet_words = ("packet", "discard", "error", "unknown", "数据包", "丢弃", "错误", "未知")
    if any(word in label for word in packet_words):
        return False
    return label in {"字节", "位元組"} or "byte" in label


def _read_network_counters() -> _NetworkCounters | None:
    system = platform.system()
    if system == "Darwin":
        return _read_macos_network_counters()
    if system == "Linux":
        return _read_linux_network_counters()
    if system == "Windows":
        return _read_windows_network_counters()
    return None


def _format_rate(bytes_per_second: float) -> str:
    units = ("B/s", "KB/s", "MB/s", "GB/s")
    value = max(0.0, float(bytes_per_second))
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B/s":
                return f"{int(round(value))} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return "0 B/s"


class SystemMetricsSampler:
    """Sample local metrics and derive rates from previous counters."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.monotonic()
        self._last_cpu = _read_linux_cpu_counters() or _read_windows_cpu_counters()
        self._last_network = _read_network_counters()
        self._last_network_time = time.monotonic()

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            sampled_at = time.time()
            system_name = platform.system()
            current_cpu = _read_linux_cpu_counters() or _read_windows_cpu_counters()
            if system_name == "Darwin":
                cpu_percent = _read_macos_cpu_percent()
            else:
                cpu_percent = _cpu_percent_from_delta(current_cpu, self._last_cpu)
                if cpu_percent is None:
                    cpu_percent = _read_load_percent()
            if current_cpu is not None:
                self._last_cpu = current_cpu

            now = time.monotonic()
            current_network = _read_network_counters()
            upload_rate = 0.0
            download_rate = 0.0
            if current_network and self._last_network:
                elapsed = max(now - self._last_network_time, 0.001)
                upload_rate = max(0.0, (current_network.sent - self._last_network.sent) / elapsed)
                download_rate = max(
                    0.0,
                    (current_network.received - self._last_network.received) / elapsed,
                )
            if current_network is not None:
                self._last_network = current_network
                self._last_network_time = now

            upload_rate_int = int(round(upload_rate))
            download_rate_int = int(round(download_rate))
            gpu_metrics = read_gpu_metrics()
            return {
                "sampled_at": sampled_at,
                "runtime": {"uptime_seconds": int(max(0.0, now - self._started_at))},
                "system": {
                    "cpu_percent": _clamp_percent(cpu_percent),
                    "memory_percent": _clamp_percent(_read_memory_percent()),
                    "gpu_percent": _clamp_percent(gpu_metrics.percent),
                    "gpu_available": gpu_metrics.available,
                    "gpu_detail": gpu_metrics.detail,
                },
                "network": {
                    "upload": {"text": _format_rate(upload_rate_int)},
                    "download": {"text": _format_rate(download_rate_int)},
                    "upload_bytes_per_sec": upload_rate_int,
                    "download_bytes_per_sec": download_rate_int,
                    "available": current_network is not None,
                },
            }


_SAMPLER = SystemMetricsSampler()


def build_system_metrics_snapshot() -> dict[str, object]:
    """Return a best-effort local metrics snapshot for the API server."""
    return _SAMPLER.snapshot()
