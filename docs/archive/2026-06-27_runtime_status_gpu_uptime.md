# Runtime Status GPU and Uptime Fix

> 时间：2026-06-27 13:07:09 +0800

## 背景

用户在轻前端右侧运行状态卡片反馈两点：

- GPU 状态显示为 `--`，无法看到真实状态。
- “本次运行”使用前端页面加载时间，每次刷新都会归零。

## 处理

- `/api/system/metrics` 增加 `runtime.uptime_seconds`，由后端 `SystemMetricsSampler` 按进程启动时间累计。
- 新增 `mediatools.system_gpu`，支持 best-effort GPU 利用率采样：
  - NVIDIA：`nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits`
  - macOS：`ioreg -r -d 1 -c IOAccelerator` 的 `Device Utilization %` / `Renderer Utilization %`
- 前端 `getSystemMetrics()` 改为消费后端 runtime，不再使用页面加载时间。
- GPU 不可采集时表盘显示 `未支持`，采集成功时显示百分比。

## 验证

- `python scripts/verify.py`（通过 `.venv/bin/python scripts/verify.py` 执行）：Python 230 passed, 6 skipped；ruff 通过；frontend 57 passed, 3 skipped；build 通过；npm audit 0 vulnerabilities。
- 临时浏览器 smoke：`http://127.0.0.1:5174/` 运行状态卡片显示 GPU 45%-51%；刷新前 0天0时1分29秒，刷新后 0天0时1分31秒，未归零。
