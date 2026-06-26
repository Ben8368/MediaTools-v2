# Current Context

> **更新时间：** 2026-06-26 17:58:50 +0800
> **当前分支：** `refactor-v2`  
> **当前阶段：** Phase 3 - 下载工作流已验收；v2 轻前端下载工作台、本地 API 适配层、统一启动脚本、前端规模门禁和 fetch CLI 兼容收口已接入并通过标准验证。
> **完整历史：** `docs/archive/03_Context_2026-06-26_full.md`

## 1. 当前状态

- 首批 MVP 已完成并通过真实样本验收：`probe`、`encode`、`subtitle`、`screenshot`、`fetch`。
- 下载工作流已完成批量 URL、dry-run、summary、原语言字幕、字幕-only、rolling 清理、句子级合并和并发锁硬化。
- `fetch` 推荐使用 `--output-dir` 指定下载目录；历史写法 `fetch <URL> <DIR>` 与 `fetch <DIR> --input-file ...` 已保留兼容并补充回归测试。
- 真实样本结果：
  - 7 URL 批量下载通过：H264+AAC+MP4 + SRT 原语言字幕。
  - 51 URL 字幕-only 通过：51 succeeded, 0 failed，仅输出 51 个 SRT。
  - macOS Chrome 登录态 playlist 前三条下载通过：H264+AAC+MP4，1080p。
- 轻前端已接入 v2 API：
  - `doctor`
  - `fetch/plan`
  - `fetch/tasks` 提交与列表
  - 任务取消、删除、清空记录
- 统一启动入口已具备：`python scripts/start.py`，支持 API + Vite 前端、`--backend-only`、自定义 host/port。
- 本轮治理目标已完成：把每轮必读文档从“全文流水账”改为“短入口 + 按需归档”。
- 标准验证已通过：Python 192 passed, 6 skipped；ruff 通过；frontend 57 passed, 3 skipped；build 通过；`npm ci` audit 0 vulnerabilities；doctor 找到 `ffmpeg`、`ffprobe`、`yt-dlp`。

## 2. 当前阻断项

- [x] 治理文档瘦身后运行 `python scripts/verify.py`。
- [x] 验证通过后同步 `04_Features.md` 与 `05_Lessons.md` 当前状态。
- [x] 当前无治理文档瘦身阻断项。

## 3. 剩余黄灯

- Legacy 前端隔离大文件仍需后续拆分或移出主源码路径。
- 真实下载中断目前主要是任务层取消；若要硬杀 `yt-dlp` 子进程，需要重构外部进程封装。
- WebSocket/SSE 推送需等任务进度模型进一步稳定。
- 轻前端仍需用户主观验收：视觉密度、排版、停止/删除/重试交互和使用路径是否贴近 Legacy。

## 4. 下一步建议

1. 进行轻前端主观验收；通过后再把用户可见轻前端功能标为完成。
2. Legacy 前端隔离大文件仍需后续拆分或移出主源码路径。
3. 下载与轻前端稳定后，再评估视频切片、资产扫描 / 搜索 / 统计。

## 5. 维护边界

- 治理文档入口保持短小；详细历史放 `docs/archive/`。
- 客观项必须先跑 `python scripts/verify.py`；主观项等待用户反馈。
- 不提交构建产物、`node_modules`、`__pycache__`、`.env`、运行日志、数据库、vendor 残留。
- 所有路径处理使用 `mediatools.core.paths`。
- 新运行时依赖默认拒绝，除非标准库或系统工具无法满足。
- 代码规模门禁：350 行预警，450 行评估拆分，500 行由 `scripts/verify.py` 硬性失败。
