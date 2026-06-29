from __future__ import annotations

from mediatools import system_gpu, system_metrics


def test_nvidia_gpu_percent_uses_busiest_device(monkeypatch) -> None:
    monkeypatch.setattr(
        system_gpu,
        "_run_tool",
        lambda command: "12\n47\n" if command[0] == "nvidia-smi" else "",
    )

    metrics = system_gpu._read_nvidia_gpu_percent()

    assert metrics is not None
    assert metrics.available is True
    assert metrics.percent == 47


def test_macos_gpu_percent_reads_ioreg_device_utilization(monkeypatch) -> None:
    ioreg_output = '"PerformanceStatistics" = {"Device Utilization %"=37}'
    monkeypatch.setattr(
        system_gpu,
        "_run_tool",
        lambda command: ioreg_output if command[0] == "ioreg" else "",
    )

    metrics = system_gpu._read_macos_gpu_percent()

    assert metrics is not None
    assert metrics.available is True
    assert metrics.percent == 37


def test_snapshot_reports_backend_uptime(monkeypatch) -> None:
    clock = iter([100.0, 100.0, 105.4])
    monkeypatch.setattr(system_metrics.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(system_metrics.platform, "system", lambda: "Linux")
    monkeypatch.setattr(system_metrics, "_read_linux_cpu_counters", lambda: None)
    monkeypatch.setattr(system_metrics, "_read_windows_cpu_counters", lambda: None)
    monkeypatch.setattr(system_metrics, "_read_load_percent", lambda: 10.0)
    monkeypatch.setattr(system_metrics, "_read_memory_percent", lambda: 20.0)
    monkeypatch.setattr(system_metrics, "_read_network_counters", lambda: None)
    monkeypatch.setattr(
        system_metrics,
        "read_gpu_metrics",
        lambda: system_gpu.GpuMetrics(percent=30.0, available=True, detail="test"),
    )

    sampler = system_metrics.SystemMetricsSampler()
    snapshot = sampler.snapshot()

    assert snapshot["runtime"] == {"uptime_seconds": 5}
    assert snapshot["system"] == {
        "cpu_percent": 10.0,
        "memory_percent": 20.0,
        "gpu_percent": 30.0,
        "gpu_available": True,
        "gpu_detail": "test",
    }


def test_snapshot_reports_network_rate(monkeypatch) -> None:
    clock = iter([100.0, 100.0, 101.0])
    counters = iter([
        system_metrics._NetworkCounters(received=1_000, sent=500),
        system_metrics._NetworkCounters(received=2_500, sent=900),
    ])
    monkeypatch.setattr(system_metrics.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(system_metrics.platform, "system", lambda: "Linux")
    monkeypatch.setattr(system_metrics, "_read_linux_cpu_counters", lambda: None)
    monkeypatch.setattr(system_metrics, "_read_windows_cpu_counters", lambda: None)
    monkeypatch.setattr(system_metrics, "_read_load_percent", lambda: 10.0)
    monkeypatch.setattr(system_metrics, "_read_memory_percent", lambda: 20.0)
    monkeypatch.setattr(system_metrics, "_read_network_counters", lambda: next(counters))
    monkeypatch.setattr(
        system_metrics,
        "read_gpu_metrics",
        lambda: system_gpu.GpuMetrics(percent=30.0, available=True, detail="test"),
    )

    sampler = system_metrics.SystemMetricsSampler()
    snapshot = sampler.snapshot()

    assert snapshot["network"] == {
        "upload": {"text": "400 B/s"},
        "download": {"text": "1.5 KB/s"},
        "upload_bytes_per_sec": 400,
        "download_bytes_per_sec": 1500,
        "available": True,
    }


def test_windows_netstat_parser_accepts_localized_bytes_row() -> None:
    counters = system_metrics._parse_windows_netstat_counter_line(
        ["字节", "2810178116", "712524367"],
    )

    assert counters == system_metrics._NetworkCounters(
        received=2810178116,
        sent=712524367,
    )


def test_windows_netstat_parser_ignores_packet_rows() -> None:
    counters = system_metrics._parse_windows_netstat_counter_line(
        ["Unicast", "packets", "151745495", "426215106"],
    )

    assert counters is None
