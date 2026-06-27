# Lessons Index

> **用途：** 每轮开局读取的压缩错题集。完整历史见 `docs/archive/05_Lessons_2026-06-26_full.md`。  
> **使用方式：** 先按任务关键词匹配主题规则；只有需要背景、时间线或原始复盘时再读归档全文。

## 1. 治理与验证

- H-001：不能只更新 `03_Context.md`；阶段、功能、重构、用户命令变更时同步检查对应文档。
- L-047：用户可见 CLI 参数迁移时同时做三件事：新写法进 README/使用指南，旧写法保留兼容或明确破坏性变更，并补回归测试覆盖历史命令。
- L-006：客观验证由 AI 执行；统一跑 `python scripts/verify.py`，用户只做主观体验和业务判断。
- L-009/L-016/L-043：代码规模规则必须进验证入口；Python 与前端源码都执行 350/450/500 行治理，历史大文件必须显式隔离。
- L-032：`🟢 完美` 不只是测试过，还要消除会误导接手者的维护预警和 CI annotation。
- L-046：最终 Audit 为 `🟢 完美` 且客观验证通过时，自动本地提交并推送；`🟡/🔴` 不自动提交。
- 本轮新增：治理文档入口保持短小；长历史归档到 `docs/archive/`，避免每轮占用过多上下文。

## 2. 跨平台与环境

- L-004：路径逻辑放 `core/paths.py`；测试使用 `tmp_path`；写入前用安全边界检查。
- L-005：README 和测试优先覆盖 `python -m mediatools`，不要依赖 console script 是否在 PATH。
- L-010/L-041：验证失败若指向用户级 site-packages、pytest temp、npm cache 权限，先按环境问题处理，可把缓存指向工作区临时目录后复跑。
- L-020：Windows 子进程输出可能不是 UTF-8；捕获文本时使用 `errors="replace"`。
- L-024：macOS 验证使用 Python 3.11+ venv，避开系统 Python 与 Homebrew 全局 pip。
- L-027：macOS 默认配置/数据/缓存目录使用 `~/Library/...`，但允许 XDG 覆盖。

## 3. 外部工具与 CLI 错误

- L-007：`ffmpeg`、`ffprobe`、`yt-dlp` 调用集中封装；参数用列表，禁止 `shell=True`；单测 mock runner，不依赖真实媒体或网络。
- L-011：本地 smoke 能补足 mock，但不能替代真实体验或主观验收。
- L-031：下载 CLI 给普通用户保守默认超时；`--timeout 0` 表示显式不限时。
- L-033：用户输入路径触发的 I/O 必须转为项目错误；CLI stderr 不应出现 Python traceback。

## 4. 下载安全与 yt-dlp

- L-012：YouTube 自动字幕需要 `--write-auto-subs`；`--write-subs` 只覆盖人工字幕。
- L-017：yt-dlp `-t mp4` / `--preset-alias mp4` 已覆盖 H264+AAC+MP4，通常无需额外转码。
- L-018/L-022：`--sub-langs original` 需用 `yt-dlp --print language` 探测；locale 语言要同时覆盖带 locale 与 base 标签。
- L-019：`--convert-subs` 是 yt-dlp 原生后处理参数，可直接透传。
- L-023：YouTube playlist 可能触发登录/反机器人；显式暴露 `--cookies` / `--cookies-from-browser`，互斥且不默认读取浏览器登录态。
- L-025：dry-run 只构造计划，不联网、不探测语言、不读取浏览器 cookie。
- L-026：批量下载 Ctrl-C 也要写 partial summary；不要自动删除 `.part`。
- L-028：友好命名模板用白名单字段编译到 yt-dlp 原生模板；dry-run 用占位符，不能触网。
- L-029/L-030：URL scheme 与 output-template 必须早于任何外部探测校验；拒绝非 http(s)、绝对路径、Windows drive path 和 `..`。
- 本轮新增：`yt-dlp --sub-langs` 参数是正则匹配，不是语言码等值匹配；`original` 探测到 `zh-CN`、`en-US` 等 locale 时必须展开为锚定正则，否则会误命中 `*-zh-CN` 这类翻译字幕并触发大量请求/429。

## 5. 字幕后处理

- L-034：下载后处理只处理本次新增/变更产物，不扫描整个输出目录。
- L-035：字幕-only 默认目标是“一个输入视频对应一个干净原语言 SRT”；优先 `*-orig`，清理 fallback 和重复文件。
- L-036：YouTube 自动字幕可能是 rolling/cumulative cue；要做内容级去重，ASS/LRC 等未知格式只读跳过。
- L-037：字幕长句合并按时间词片切分；有词边界时控制 `max_duration_ms`，CJK 等无空格语言暂不强行单字切分。

## 6. 轻前端与 API

- L-008：前后端分离不是问题，过早分离才是问题；核心契约稳定后再扩展 UI/API。
- L-015/L-038：Legacy UI 适合壳层移植，不适合整包回流；保留空间记忆，旧 API、重型功能和平台耦合不直接迁移。
- L-039：当前轻前端 API 可用 Python stdlib HTTP server 支撑，无需先引入 Flask/FastAPI。
- L-040：任务模型增长时拆出 `api_tasks.py`；API server 只保留路由、请求解析和调度。
- L-042：统一启动脚本传递端口契约与环境变量，不修改配置文件。
- L-044/L-045：常驻壳层、日志、通知等高频入口不能暴露 Legacy 占位；接 v2 端点或返回安静空态。
- 本轮新增：用户高频路径选择不能停留在临时输入框或 Legacy 占位；前端选择器、API 契约、后端目录浏览/新建能力和提交 payload 要一次接通，并补端到端表单测试。
- 本轮新增：CLI 已支持的认证参数不能在轻前端丢失；YouTube 登录/反机器人失败应通过显式 `cookies_from_browser` 选择器解决，不默认读取浏览器登录态。
- 本轮新增：可见运行指标不能在前端硬编码为 0；CPU、内存、网络这类状态应由 v2 后端提供 best-effort 快照，采集失败再安静降级。
- 本轮新增：常驻运行时间不能用前端页面加载时间推导；应由后端进程提供累计 uptime，刷新页面后仍保持连续。GPU 等平台指标优先 best-effort 采样（如 macOS IOAccelerator、NVIDIA nvidia-smi），不可采时明确显示未支持。
- 本轮新增：前端可见动作不能用本地假成功代替后端契约；“关闭”这类系统级操作必须调用 v2 API，由启动脚本/父进程负责收尾相关服务。
- 本轮新增：前端下载任务产物时，任务结果必须记录具体文件路径而不是输出目录；下载 API 只允许读取已登记任务产物，避免把任意本机路径暴露给前端。
- 本轮新增：高频提交动作不能等待后台列表刷新才恢复 UI；后端返回任务 ID 后应立即插入乐观任务并收起表单，列表刷新失败或变慢只能影响同步精度，不能让用户误以为按钮没反应。
- 本轮新增：前端 API 请求需要有用户可读的无响应超时提示；否则后端停止、代理卡住或网络异常会表现为“点击后没反应”。

## 7. 数据与仓库卫生

- L-001：调整 `.gitignore` 后，用 `git status --short --branch` 和 `git ls-files --others --exclude-standard` 共同确认未跟踪文件。
- L-013：未知本地数据先归档，不直接删除；明确生成物、缓存、coverage、重复下载可以清理。
- L-014：`.agents/` 为空不是健康问题；没有工具专属规则时不强行填充。

## 8. 已固化到规则或代码的经验

- `02_AI_Rules.md`：编码、路径、子进程、错误处理、验证、前后端边界、红绿灯审查。
- `scripts/verify.py`：安装、测试、ruff、doctor、Python/前端源码规模门禁。
- `docs/archive/05_Lessons_2026-06-26_full.md`：完整错题历史和背景。
