# Current Context

> **更新时间：** 2026-06-27 19:15:46 +0800
> **当前分支：** `refactor-v2`  
> **当前阶段：** Phase 3 - 下载工作流已验收；v2 轻前端下载工作台、本地 API 适配层、下载保存目录选择器、运行状态面板、统一启动脚本、前端规模门禁、fetch CLI 兼容和前端配置维护风险收口已接入并通过标准验证。
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
  - `workspace` 与最小 `filebrowser` 端点，用于下载表单选择/新建保存目录
  - `system/metrics` CPU、内存、GPU、网络速率与后端累计运行时长快照
- 统一启动入口已具备：`python scripts/start.py`，支持 API + Vite 前端、`--backend-only`、自定义 host/port。
- 前端维护风险已收口：Vite 配置统一保留 `frontend/vite.config.ts`，并合并原 JS 配置中的 HMR 设置；未引用的 `frontend/public/static/app/index.js` 构建产物残留已移除。
- 专题文档状态已收口：`01_Project_Plan.md`、`REFACTOR.md`、`docs/DOWNLOADER_USAGE.md`、`docs/UI_API_CONTRACT.md`、AI co-author 文档与当前实现/规范对齐；旧前后端接通报告已归档到 `docs/archive/2026-06-25_frontend_cleanup_report.md`。
- 本轮治理目标已完成：把每轮必读文档从“全文流水账”改为“短入口 + 按需归档”。
- 下载表单的目标目录已从临时输入框改为真实目录选择器；支持浏览本机磁盘/目录、粘贴路径、新建文件夹，并把所选路径作为 `output_dir` 提交给下载任务。
- 标准验证已通过：Python 238 passed, 6 skipped；ruff 通过；frontend 58 passed, 3 skipped；build 通过；`npm ci` audit 0 vulnerabilities；doctor 找到 `ffmpeg`、`ffprobe`、`yt-dlp`。
- 右侧运行状态面板已从 v2 `/api/system/metrics` 读取 CPU、内存、GPU、网络速率与后端累计运行时间；浏览器 smoke 显示 GPU 45%-51%，刷新前 0天0时1分29秒、刷新后 0天0时1分31秒，未再归零。

## 2. 当前阻断项

- [x] 治理文档瘦身后运行 `python scripts/verify.py`。
- [x] 验证通过后同步 `04_Features.md` 与 `05_Lessons.md` 当前状态。
- [x] 下载保存目录选择器接入 v2 文件浏览端点，并通过 `python scripts/verify.py` 标准验证。

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
