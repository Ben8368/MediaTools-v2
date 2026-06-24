# Feature Pool and ADR

## 1. 功能评估原则

所有功能进入实现前，必须先经过轻量评估：

- **用户价值**：是否解决真实高频问题。
- **技术依赖**：是否依赖未确认技术栈或大型外部工具。
- **跨平台影响**：是否在 Windows / macOS / Linux 有不同表现。
- **安全影响**：是否涉及文件写入、路径遍历、外部命令、网络下载或凭据。
- **测试方式**：是否能用自动化测试覆盖核心逻辑。

状态标记：
- `[待评估]`：只有想法，还不能实现。
- `[待决策]`：需要用户或技术栈选择。
- `[待实现]`：已具备实现条件。
- `[待验证]`：代码或文档已改，等待用户验证。
- `[客观已验证]`：本地验证和必要的自动化检查已通过，仍可能等待用户体验验收或 CI 复核。
- `[已完成]`：客观验证通过，且必要的用户体验验收或阶段决策已确认。

## 2. 候选功能

### Feature-001：核心功能清单梳理
- **提交时间：** 2026-06-24
- **类型：** 治理/规划
- **描述：** 从 Legacy 版本中识别真正需要迁移的核心能力，形成首批 MVP 功能清单。
- **用户价值：** 避免无差别搬运旧系统，降低重构范围失控风险。
- **前置依赖检查：**
  - 技术依赖：无
  - 环境依赖：可读取 Legacy 仓库或远程参考
  - 安全影响：只读分析
  - 跨平台兼容性：需标注每个功能的跨平台风险
- **预计影响模块：**
  - 文档：`04_Features.md`、`03_Context.md`
  - 后续源码：由技术栈决策后确定
- **验证思路：**
  - 用户确认首批 MVP 功能排序
  - 每个功能都包含验收标准和回滚策略
- **状态：** [已完成] - 用户确认首批 MVP = A/B/C/D/E（probe / 转码 / 字幕转换 / 截图 / 下载），完整 Tier 矩阵见 §3，对应 Feature-005~009

### Feature-002：Legacy 迁移策略
- **提交时间：** 2026-06-24
- **类型：** 架构/迁移
- **描述：** 建立从 Legacy 版本提取业务逻辑、测试样例和工作流的迁移流程，同时拒绝 vendor、缓存、构建产物和过度抽象直接进入 v2。
- **用户价值：** 复用已验证经验，但保持新仓库干净可维护。
- **前置依赖检查：**
  - 技术依赖：已确认 Python CLI 优先
  - 环境依赖：Legacy 仓库作为只读参考
  - 安全影响：避免复制示例密钥、历史大文件、第三方 vendor
  - 跨平台兼容性：迁移时优先保留跨平台实现
- **预计影响模块：**
  - 文档：`REFACTOR.md`、`03_Context.md`
  - 脚手架：按最终技术栈确定
- **验证思路：**
  - 每次迁移只引入一个小功能
  - 先写测试或样例，再实现
  - `git status` 不出现 vendor、运行数据或构建产物
- **状态：** [已完成] - 已确认 Python CLI 优先；Phase 2 按小功能、mock 测试、拒绝 vendor 的方式迁移首批 MVP

### Feature-003：跨平台路径处理模块
- **提交时间：** 2026-06-24
- **类型：** 核心功能
- **描述：** 统一的跨平台路径处理，避免 Windows/Unix 差异。
- **用户价值：** 保证工具在所有平台上表现一致。
- **前置依赖检查：**
  - 技术依赖：需完成技术栈初始化
  - 环境依赖：跨平台测试环境
  - 安全影响：路径遍历安全检查
  - 跨平台兼容性：核心目标
- **预计影响模块：**
  - 源码：`src/mediatools/core/paths.py`
  - 测试：`tests/test_paths.py`
  - 文档：`02_AI_Rules.md` §4
- **验证思路：**
  - 自动化测试：覆盖绝对路径、相对路径、路径拼接、规范化
  - 跨平台验证：Windows/macOS/Linux CI 矩阵
  - 回归范围：所有使用路径的模块
- **降级/回滚策略：** 使用标准库原生 API
- **状态：** [已完成] - 本地 9 passed + ruff；CI ubuntu/windows/macos 绿灯（run #28076101163）

### Feature-004：最小 CLI 脚手架
- **提交时间：** 2026-06-24
- **类型：** 工程初始化
- **描述：** 在技术栈确认后建立最小可运行入口、依赖声明、测试入口和 README 运行命令。
- **用户价值：** 让 v2 从文档阶段进入可执行、可验证阶段。
- **前置依赖检查：**
  - 技术依赖：主语言、测试框架、依赖管理方式
  - 环境依赖：本机运行环境
  - 安全影响：不访问网络、不执行破坏性命令
  - 跨平台兼容性：入口命令需避免平台特定 shell 语法
- **预计影响模块：**
  - 源码：按技术栈确定
  - 测试：最小 smoke test
  - 文档：README 安装和运行说明
- **验证思路：**
  - 干净 checkout 后能安装依赖
  - 一个命令能运行测试
  - 一个命令能显示 CLI 帮助或版本
- **状态：** [已完成] - 用户已验证 `python -m mediatools`、`pytest`、`ruff` 通过

### Feature-005：媒体信息探测 (probe) — MVP-A
- **提交时间：** 2026-06-24
- **类型：** 核心功能 / Tier 1 P0
- **描述：** 调用 `ffprobe` 读取媒体文件元信息：时长、分辨率、编码格式、码率、流信息，输出结构化结果（文本 + `--json`）。
- **用户价值：** 所有媒体工作流的地基，转码/截图/切片都需要先探测；高频只读操作。
- **Legacy 来源：** `modules/fetcher/analyzer`、`backend/services/media/core`
- **前置依赖检查：**
  - 技术依赖：系统 `ffprobe`（随 ffmpeg 分发），`shutil.which()` 探测，复用 `doctor` 模式
  - 环境依赖：用户本机 PATH 中的 ffmpeg/ffprobe
  - 安全影响：只读；输入路径须 `normalize()`；禁止 `shell=True`
  - 跨平台兼容性：子进程参数列表调用，跨平台一致
- **预计影响模块：**
  - 源码：`src/mediatools/core/ffmpeg.py`（子进程封装）、`src/mediatools/core/probe.py`（解析逻辑）
  - CLI：`src/mediatools/cli.py` 注册 `probe` 子命令
  - 测试：`tests/test_probe.py`（mock 子进程输出）
- **验证思路：**
  - 单元测试 mock `ffprobe` JSON 输出，断言解析正确
  - ffprobe 缺失时给出可读报错（ExternalToolError）
- **降级/回滚策略：** ffprobe 不可用时明确提示安装 ffmpeg，不静默失败
- **状态：** [已完成] - 已实现 `core/ffmpeg.py` + `core/probe.py` + `probe` CLI；本地验证、CI 三平台、生成媒体 smoke、真实视频样本 probe 均通过

### Feature-006：转码 / 音频提取 (encode) — MVP-B
- **提交时间：** 2026-06-24
- **类型：** 核心功能 / Tier 1 P0
- **描述：** 调用 `ffmpeg` 完成常见格式转换与音频提取（如 mp4→mp4 H.265、提取 mp3/aac），暴露常用参数（编码器、码率、输出格式）。
- **用户价值：** 媒体处理核心刚需，使用频率最高。
- **Legacy 来源：** `modules/encoder/transcoder`、`backend/services/encoder`、`backend/services/media/encoding`
- **前置依赖检查：**
  - 技术依赖：系统 `ffmpeg`
  - 环境依赖：用户本机 ffmpeg
  - 安全影响：写文件操作前 `is_safe_child()` 校验输出目录；禁止覆盖未确认；禁止 `shell=True`
  - 跨平台兼容性：参数列表调用，路径经 `paths` 模块处理
- **预计影响模块：**
  - 源码：复用 `core/ffmpeg.py`、新增 `src/mediatools/core/encode.py`
  - CLI：注册 `encode` 子命令
  - 测试：`tests/test_encode.py`（构建命令参数断言 + mock 执行）
- **验证思路：**
  - 单元测试断言生成的 ffmpeg 参数正确
  - 捕获返回码与超时，错误信息可读
- **降级/回滚策略：** 失败保留原文件，输出到独立目录，不就地破坏
- **状态：** [已完成] - 已实现 `core/encode.py` + `encode` CLI，复用 ffmpeg 封装；本地验证、CI 三平台、短真实视频转码与音频提取均通过

### Feature-007：字幕格式转换 VTT↔SRT (subtitle) — MVP-C
- **提交时间：** 2026-06-24
- **类型：** 核心功能 / Tier 1 P1
- **描述：** 纯逻辑实现 VTT 与 SRT 互转，含时间轴解析、序号重排、基础清洗（去除冗余标签）。
- **用户价值：** 高频字幕处理；零外部依赖；是验证「core 纯逻辑 + CLI 适配层」分层架构的最佳样板。
- **Legacy 来源：** `modules/fetcher/subtitle`、`backend/services/workbench`（仅格式转换部分，不含 AI 分析）
- **前置依赖检查：**
  - 技术依赖：**无**（纯标准库）
  - 环境依赖：无
  - 安全影响：文件读写显式 `encoding="utf-8"`；输入路径 `normalize()`
  - 跨平台兼容性：纯逻辑，行尾符须统一处理（`\r\n` / `\n`）
- **预计影响模块：**
  - 源码：`src/mediatools/core/subtitle.py`（纯函数解析/序列化）
  - CLI：注册 `subtitle convert` 子命令
  - 测试：`tests/test_subtitle.py`（纯函数，覆盖率高）
- **验证思路：**
  - 单元测试：VTT→SRT、SRT→VTT 往返一致性
  - 边界：空行、多行字幕、特殊时间格式、BOM
- **降级/回滚策略：** 不修改源文件，输出新文件
- **状态：** [已完成] - 已实现 `core/subtitle.py` + `subtitle convert` CLI；覆盖 VTT↔SRT、BOM、标签清洗、时间轴序列化；本地验证、CI 三平台、真实 VTT/SRT 转换均通过

### Feature-008：视频截图 / 抽帧 (screenshot) — MVP-D
- **提交时间：** 2026-06-24
- **类型：** 核心功能 / Tier 1 P1
- **描述：** 调用 `ffmpeg` 从视频指定时间点截图，或按间隔批量抽帧，输出图片到指定目录。
- **用户价值：** 常用且实现简单，与转码共用 ffmpeg 基础设施。
- **Legacy 来源：** `modules/generator/screenshot`
- **前置依赖检查：**
  - 技术依赖：系统 `ffmpeg`
  - 环境依赖：用户本机 ffmpeg
  - 安全影响：输出目录 `is_safe_child()` 校验；禁止 `shell=True`
  - 跨平台兼容性：参数列表调用
- **预计影响模块：**
  - 源码：复用 `core/ffmpeg.py`、新增 `src/mediatools/core/screenshot.py`
  - CLI：注册 `screenshot` 子命令
  - 测试：`tests/test_screenshot.py`（命令参数断言 + mock）
- **验证思路：**
  - 单元测试断言时间点/间隔参数转换正确
  - 时间格式校验（HH:MM:SS / 秒）
- **降级/回滚策略：** 输出到独立目录，不覆盖已有图片
- **状态：** [已完成] - 已实现 `core/screenshot.py` + `screenshot` CLI，支持指定时间点与间隔抽帧；本地验证、CI 三平台、真实视频截图均通过

### Feature-009：视频 / 字幕下载 (fetch) — MVP-E
- **提交时间：** 2026-06-24
- **类型：** 核心功能 / Tier 2 P2
- **描述：** 封装 `yt-dlp` 完成视频与字幕下载，把 yt-dlp 作为系统外部工具探测调用（同 ffmpeg 模式，**不 vendor 第三方源码**）。
- **用户价值：** 媒体获取入口，价值高；是完整工作流（下载→转码→字幕）的起点。
- **Legacy 来源：** `modules/fetcher/downloader`、`modules/fetcher/ytdlp_manager`、`modules/fetcher/csv_manager`
- **前置依赖检查：**
  - 技术依赖：系统 `yt-dlp`（PATH 探测，不 vendor）；需在 `doctor` 中增加 yt-dlp 探测
  - 环境依赖：网络访问；用户本机 yt-dlp
  - 安全影响：**网络下载需安全审查**——URL 校验、下载目录 `is_safe_child()`、不执行下载内容、不泄露凭据；禁止 `shell=True`
  - 跨平台兼容性：参数列表调用；文件名跨平台清洗（非法字符）
- **预计影响模块：**
  - 源码：`src/mediatools/core/fetch.py`（yt-dlp 封装）
  - CLI：注册 `fetch` 子命令
  - 测试：`tests/test_fetch.py`（mock yt-dlp，不实际联网）
  - 文档：`doctor` 增加 yt-dlp 探测、README 说明外部依赖
- **验证思路：**
  - 单元测试 mock 子进程，断言命令参数与文件名清洗
  - yt-dlp 缺失时可读报错
- **降级/回滚策略：** yt-dlp 不可用时提示安装，不静默失败；下载失败清理半成品
- **状态：** [已完成] - 已实现 `core/fetch.py` + `fetch` CLI，yt-dlp 作为 PATH 系统工具探测，限制 http/https URL；本地 mock 验证、CI 三平台、真实 YouTube 视频下载通过；真实样本发现自动字幕需求并补充 `--write-auto-subs`

### Feature-010：下载工作流增强 (fetch workflow) — Phase 3-A
- **提交时间：** 2026-06-24
- **类型：** 核心功能增强 / Phase 3 P0
- **描述：** 在现有 `fetch` MVP 基础上完善真实落地体验，包括批量 URL、字幕语言选择、人工字幕/自动字幕区分、登录态 cookie 透传、dry-run 预览、下载结果摘要、失败清单、元数据保存和已存在文件跳过策略。
- **用户价值：** 下载是媒体工作流入口；真实使用中最容易暴露网络、字幕、命名、失败恢复和批量管理问题，优先完善能让工具更快进入日常使用。
- **Legacy 来源：** `modules/fetcher/downloader`、`modules/fetcher/ytdlp_manager`、`modules/fetcher/csv_manager`、旧前端下载任务流。
- **前置依赖检查：**
  - 技术依赖：复用系统 `yt-dlp` 与现有 `core/fetch.py`；优先不引入新运行时依赖。
  - 环境依赖：真实下载依赖网络与站点可用性；自动化测试仍使用 mock，不访问网络。
  - 安全影响：批量 URL 需逐条校验 http/https；输出目录继续使用安全边界；不得执行下载内容；失败日志不得泄露凭据。
  - 跨平台兼容性：路径、文件名、CSV/TXT 编码必须跨平台；输出摘要使用 UTF-8。
- **预计影响模块：**
  - 源码：`src/mediatools/core/fetch.py`，必要时新增下载计划/结果模型。
  - CLI：扩展 `fetch` 参数，可能新增 `fetch batch` 或 `--input-file`。
  - 测试：扩展 `tests/test_fetch.py`，覆盖批量解析、dry-run、字幕参数和失败摘要。
  - 文档：README 下载示例、`03_Context.md`、本功能条目。
- **验收思路：**
  - mock 测试覆盖命令参数构造、批量输入解析、错误摘要、跳过策略。
  - 本地真实样本体验验证覆盖：单 URL、批量 URL、人工字幕、自动字幕、无字幕、下载失败。
- **降级/回滚策略：** 保留现有单 URL `fetch` 行为；增强功能以新增参数或子命令提供，不破坏现有命令。
- **状态：** [已完成] - 已实现批量 URL 输入、dry-run、summary JSON、info JSON、download archive、登录态 cookie 透传（`--cookies` / `--cookies-from-browser`）；真实 7 URL 批量下载体验验收通过；macOS playlist 校验发现 YouTube 登录态阻断并已补强认证参数；当前标准验证 84 passed, 3 skipped；ruff 通过；doctor 通过；CI #28096484531 三平台绿灯

### Feature-011：Legacy 风格轻前端 / 下载工作台 — Phase 3-B
- **提交时间：** 2026-06-24
- **类型：** UI / 适配层 / Phase 3 P1
- **描述：** 在不恢复 Legacy 复杂架构的前提下，建立可边开发边使用的本地轻前端。前端优先服务下载工作台，并保持 Legacy 的布局、视觉节奏和用户路径，降低老用户学习成本。
- **用户价值：** CLI 已能验证核心能力，但日常下载、批量任务和结果查看更适合图形界面；贴近 Legacy 的 UI 能让用户快速迁移。
- **Legacy 来源：** 旧前端源码、截图、运行界面、用户熟悉的导航和任务布局。当前 v2 `frontend/` 仅有未跟踪构建/依赖残留，不能直接作为源码基线。
- **前置依赖检查：**
  - 技术依赖：先考古 Legacy 技术栈；若 Legacy 使用 Vite / React / TypeScript 或相近方案，v2 优先采用相近方案。
  - 环境依赖：Node.js 前端工具链仅在进入前端工程后引入；不提交 `node_modules`、`.vite`、`dist`。
  - 安全影响：前端不得直接执行任意命令；所有任务必须经受控 API / CLI 适配层；输出目录选择需沿用安全边界。
  - 跨平台兼容性：本地 Web UI 优先；桌面壳（Electron/Tauri）等到工作流稳定后再评估。
- **预计影响模块：**
  - 文档：`docs/UI_COMPAT.md`，README，治理文档。
  - 后端适配：未来可能新增最小 API / 任务进度模型。
  - 前端：待 Legacy 考古后初始化。
- **验收思路：**
  - 先形成 Legacy UI 兼容基线，再实现下载工作台。
  - 前端首屏能完成 URL 输入、批量导入、字幕选项、输出目录、任务状态和结果查看。
  - 前端构建/测试纳入标准验证或独立前端验证脚本。
- **降级/回滚策略：** 若前端工程引入风险过大，保留 CLI 下载增强作为主路径；轻前端只作为可选本地入口。
- **状态：** [待评估] - 已建立 `docs/UI_COMPAT.md` 作为准入基线，下一步需考古 Legacy 技术栈

### Feature-012：下载格式控制与原语言探测 — Phase 3-A+
- **提交时间：** 2026-06-24
- **类型：** 核心功能增强 / Phase 3 P0+
- **描述：** 在 `fetch` 中加入格式与原语言控制能力：`--preset mp4`（等同于 `-t mp4`，强制 H264+AAC+MP4）；`--merge-format`/`--remux-video` 细粒度控制容器格式；`--convert-subs` 自动转换字幕格式（支持 srt/vtt/ass/lrc）；`--sub-langs original` 魔术值，自动探测视频原语言并只下载原语言字幕（探测失败时降级到 `all`）。
- **用户价值：** 用户下载视频后不再需要手动转码或手动转字幕格式；`--preset mp4` 一行命令满足"最佳画质+H264+AAC+MP4"的普遍需求；`--sub-langs original` 避免下载数十种机器翻译字幕。
- **前置依赖检查：**
  - 技术依赖：复用系统 `yt-dlp`；`--preset mp4` 和 `--convert-subs srt` 均为 yt-dlp 原生参数，无需额外工具。
  - 环境依赖：语言探测需要网络（`yt-dlp --print language`），仅在网络下载流程中触发；测试用 mock，不联网。
  - 安全影响：探测仅下载元数据，不执行下载内容；格式参数为 yt-dlp 已有功能，行为可控。
  - 跨平台兼容性：字幕文件名含语言码（如 `en-US`、`ja`），无平台特定问题。
- **预计影响模块：**
  - 源码：`src/mediatools/core/fetch.py` — `FetchOptions` 扩展字段、`probe_language()`、`_resolve_sub_langs()`、`build_fetch_args` 追加新参数。
  - CLI：`src/mediatools/cli.py` — `fetch` 命令新增 `--preset`/`--merge-format`/`--remux-video`/`--convert-subs`/`--format-sort` 参数。
  - 测试：`tests/test_fetch.py` — 新增 11 个测试覆盖新参数与语言解析逻辑。
  - 文档：`03_Context.md`、`04_Features.md`、`05_Lessons.md`。
- **验收思路：**
  - mock 测试：新参数构建、`original` 解析为探测结果、探测失败降级为 `all`、`probe_language` 错误处理、`make_fetch_options` 字段透传。
  - 本地真实验收命令示例：
    ```
    mediatools fetch <URL> <DIR> --preset mp4 --write-subs --write-auto-subs \
      --sub-langs original --convert-subs srt --write-info-json
    ```
- **降级/回滚策略：** 所有新参数完全可选；不指定时行为与 Feature-010 完全一致；`original` 探测失败自动降级到 `all`；不影响现有用户工作流。
- **状态：** [已完成] - 真实 7 URL 批量下载验收通过（H264+AAC+MP4 + SRT 原语言字幕；tr/en-US/pt-BR/ar 全部正确）；发现并修复 3 个 Bug（UnicodeDecodeError、--sub-langs 重复、locale 字幕标签不匹配）；playlist 原语言探测已处理多行输出并透传 cookie 来源；当前标准验证 84 passed, 3 skipped；ruff 通过；doctor 通过；CI #28096484531 三平台绿灯

### Feature-013：macOS 兼容性补强 — Phase 3-A Hardening
- **提交时间：** 2026-06-25
- **类型：** 兼容性 / 开发体验 / 下载工作流硬化
- **描述：** 针对 macOS 常见环境与真实下载体验补强：`verify.py` 提前检查 Python 3.11+ 并对 Homebrew PEP 668 环境给出 venv 提示；README 增加 macOS venv 验证路径；`fetch --dry-run --sub-langs original` 不再触发 yt-dlp 语言探测或浏览器 cookie 读取；批量下载中 Ctrl-C 会记录中断项并允许 CLI 写出 partial summary；macOS 默认配置目录改为 `~/Library/Application Support` 与 `~/Library/Caches`。
- **用户价值：** 降低 macOS 初次验证和日常下载的摩擦，减少 dry-run 意外联网、登录态读取和中断后无摘要的问题。
- **前置依赖检查：**
  - 技术依赖：无新增运行时依赖；继续使用标准库与系统外部工具。
  - 环境依赖：macOS 推荐 Python 3.11+ 虚拟环境；媒体能力仍依赖 PATH 中的 ffmpeg/ffprobe/yt-dlp。
  - 安全影响：dry-run 不再为了 `original` 读取浏览器 cookie；中断摘要不执行或清理下载内容。
  - 跨平台兼容性：Linux/Unix 仍保留 XDG 默认目录，Windows 仍使用 LOCALAPPDATA，macOS 单独使用原生 Library 路径。
- **预计影响模块：**
  - 源码：`scripts/verify.py`、`src/mediatools/core/fetch.py`、`src/mediatools/core/config.py`。
  - 测试：`tests/test_fetch.py`、`tests/test_config.py`。
  - 文档：`README.md`、`03_Context.md`、`04_Features.md`、`05_Lessons.md`。
- **验收思路：**
  - 单元测试覆盖 dry-run 不探测语言、KeyboardInterrupt 记录失败项、macOS 默认目录。
  - 标准验证覆盖全量 pytest、ruff、doctor 和文件行数限制。
- **降级/回滚策略：** 配置目录变更仅影响未来未显式设置 XDG 的 macOS 默认路径；用户仍可通过 XDG 环境变量覆盖。下载中断只新增摘要记录，不改变已下载文件。
- **状态：** [客观已验证] - macOS 临时 venv 中 `python scripts/verify.py` 通过：86 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`

### Feature-014：下载文件名自动友好模板 — Phase 3-A Naming
- **提交时间：** 2026-06-25
- **类型：** 核心功能增强 / 下载工作流体验
- **描述：** 默认启用友好命名模板 `{lang}-{author}-{title}-{platform}.{ext}`。真实下载前根据链接自动探测语言并映射为 `KR`、`EN`、`JP`、`SC`、`TC`、`AR`、`PT` 等短码；作者、标题、平台名由 yt-dlp 元数据自动填充。保留 `--name-template` 调整字段顺序、`--name-language` 手动覆盖语言码，以及高级 `--output-template` 原生模板覆盖能力。
- **用户价值：** 用户可按语言、作者、标题、平台统一归档下载文件，批量下载后更容易排序、检索和交给后续剪辑/字幕流程使用。
- **前置依赖检查：**
  - 技术依赖：无新增运行时依赖；友好模板编译为 yt-dlp 原生输出模板。
  - 环境依赖：真实下载仍依赖 PATH 中的 `yt-dlp`；自动语言码探测复用 `yt-dlp --print language`，dry-run 不触网并以 `AUTO` 预览。
  - 安全影响：模板字段白名单校验，语言码仅允许字母、数字、`-`、`_`；模板字面量继续做跨平台字符清洗；默认传递 `--windows-filenames` 处理作者名/标题名中的本地不可用字符。
  - 跨平台兼容性：不硬编码路径分隔符；扩展名默认使用 `{ext}`，也允许用户显式写 `.mp4`。
- **预计影响模块：**
  - 源码：`src/mediatools/core/fetch_naming.py`、`src/mediatools/core/fetch.py`。
  - CLI：`src/mediatools/cli.py` — `fetch` 新增 `--name-template` / `--name-language` / `--no-windows-filenames`，并让 `--output-template` 覆盖友好模板。
  - 测试：`tests/test_fetch_naming.py`、`tests/test_fetch.py`、`tests/test_cli.py`。
  - 文档：`README.md`、`03_Context.md`、`04_Features.md`、`05_Lessons.md`。
- **验收思路：**
  - 单元测试覆盖默认模板、字段顺序调整、自动补 `{ext}`、硬编码 `.mp4`、未知字段报错、语言码自动映射与手动覆盖。
  - CLI dry-run 摘要验证默认 `AUTO-作者-标题-平台` 模板、字段重排、`--output-template` 覆盖和 `--windows-filenames` 参数。
- **降级/回滚策略：** 所有新增参数均为可选；不使用 `--name-template` 时沿用既有 `--output-template` 行为。
- **状态：** [客观已验证] - macOS venv 中 `python scripts/verify.py` 通过：106 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`

## 3. 首批 MVP 优先级矩阵

> **决策状态：** 用户已确认首批 MVP = A/B/C/D/E（2026-06-24），对应 Feature-005~009。
> Tier 来源：从 Legacy 模块结构（本地 `.pyc` + GitHub README + `runtime/workspace.json` 工作流管线）还原分析。

### 🟢 Tier 1 — 首批 MVP 第一梯队（仅依赖 ffmpeg / 标准库）

| 代号 | 功能 | 优先级 | 依赖 | 跨平台 | 可测试性 | Feature |
| --- | --- | --- | --- | --- | --- | --- |
| A | 媒体信息探测 probe | P0 | ffprobe | ✅ | 高 | Feature-005 |
| B | 转码 / 音频提取 | P0 | ffmpeg | ✅ | 高 | Feature-006 |
| C | 字幕转换 VTT↔SRT | P1 | 无 | ✅ | 极高 | Feature-007 |
| D | 视频截图 / 抽帧 | P1 | ffmpeg | ✅ | 高 | Feature-008 |

### 🟡 Tier 2 — 首批 MVP 第二梯队（依赖较重）

| 代号 | 功能 | 优先级 | 依赖 | 说明 | Feature |
| --- | --- | --- | --- | --- | --- |
| E | 视频 / 字幕下载 | P2 | yt-dlp | 含网络/安全审查，作为系统工具探测 | Feature-009 |
| F | 视频切片（单/批量） | P2 | ffmpeg | 转码自然延伸，排在下载落地与轻前端之后 | 待补 |
| G | 资产扫描 / 搜索 / 统计 | P3 | 无 | 批处理工作流基础，排在下载落地与轻前端之后 | 待补 |

### 🔴 Tier 3 — 暂缓（依赖 LLM / 重型 / 法律安全顾虑）

- 字幕 AI 分段分析（workbench）— 需 LLM API key，非纯逻辑
- 媒体解密（decryptor）— 需 Unlock Music CLI，有法律/安全顾虑
- 截图配图 / 微信朋友圈（generator 部分）— 需图像合成库，可能突破最小依赖

### ⚪ Tier 4 — 不纳入 CLI MVP（与当前架构原则冲突）

- Adobe PS/AE 自动化、CapCut 联动 — 平台特定 / vendored 工具
- AI 助手、浏览器控制、filebrowser、完整 Web 基础设施 — 仍暂缓；Phase 3 的 Legacy 风格下载工作台不属于此类完整平台化恢复

## 4. Phase 3 优先级矩阵

| 代号 | 功能 | 优先级 | 依赖 | 说明 | Feature |
| --- | --- | --- | --- | --- | --- |
| P3-A | 下载工作流增强 | P0 | yt-dlp | 批量、字幕、dry-run、结果摘要、失败清单 | Feature-010 |
| P3-A+ | 下载格式控制与原语言探测 | P0+ | yt-dlp | preset mp4、convert-subs、sub-langs original | Feature-012 |
| P3-A Hardening | macOS 兼容性补强 | P0 | 标准库 | venv 验证提示、dry-run 不联网、中断摘要、macOS Library 目录 | Feature-013 |
| P3-A Naming | 下载文件名自动友好模板 | P0 | yt-dlp | 自动语言码、字段顺序模板、Windows 兼容文件名、保留 output-template | Feature-014 |
| P3-B | Legacy 风格轻前端 / 下载工作台 | P1 | 待 Legacy 考古 | 先兼容布局和用户路径，再选技术栈 | Feature-011 |
| P3-C | 视频切片 | P2 | ffmpeg | 下载落地后再评估 | 待补 |
| P3-D | 资产扫描 / 搜索 / 统计 | P3 | 标准库优先 | 服务批处理和前端结果管理 | 待补 |

## 5. 架构决策记录 (ADR)

### ADR-001：治理文件体系
- **决策时间：** 2026-06-24
- **上下文：** 需要多 AI 工具协作，防止知识遗失。
- **决策：** 采用 01-05 治理文档 + AGENTS.md 入口。
- **后果：** AI 有记忆、可审查、可回溯；需维护文档同步。
- **状态：** 已接受

### ADR-002：全新 orphan 分支重构
- **决策时间：** 2026-06-24
- **上下文：** Legacy 版本有大文件、vendor 依赖、密钥检测问题。
- **决策：** 使用 orphan 分支全新开始，Legacy 作为备份参考。
- **后果：** 干净的 git 历史，但需要重新实现功能。
- **状态：** 已接受

### ADR-003：技术栈确认前不初始化完整工程
- **决策时间：** 2026-06-24
- **上下文：** 当前仓库目标是精简重构，过早引入前后端或大型框架会重复 Legacy 的复杂度。
- **决策：** 先完成技术栈访谈，再创建最小可运行脚手架。
- **后果：** 短期只有治理文档；长期避免错误架构先入为主。
- **状态：** 已接受

### ADR-004：Phase 1 采用 Python CLI 优先
- **决策时间：** 2026-06-24
- **上下文：** v2 的近期目标是快速建立小巧、跨平台、可测试的媒体工具核心，而不是立即恢复前后端分离架构。
- **决策：** 使用 Python 3.11+、标准库 `argparse`、`pyproject.toml`、`pytest` 和 `ruff` 初始化最小 CLI 工程。
- **后果：** 媒体处理和脚本迁移成本低；Web UI、桌面 GUI、单文件分发推迟到核心能力稳定后评估。
- **状态：** 已接受

### ADR-005：前后端分离延后到核心契约稳定后
- **决策时间：** 2026-06-24
- **上下文：** Legacy 的问题不是“有前端”，而是在核心媒体工作流、接口契约和依赖边界尚未收敛时，同时引入前后端分离、vendor 依赖和过度抽象。
- **决策：** Phase 2/早期 Phase 3 继续保持 Python CLI 优先；core 与适配层严格解耦，为未来 API / Web UI / 桌面 GUI 预留边界，但不提前初始化完整前后端工程。
- **进入 Web/UI 评估的条件：** 首批 CLI 工作流经真实媒体样本验收；CI 三平台绿灯；输入/输出/错误/进度模型稳定；存在明确的可视化批处理或多任务管理需求。
- **后果：** 当前复杂度受控，同时未来仍可通过 API 适配层自然演进到前后端分离。
- **状态：** 已接受

### ADR-006：Phase 3 优先完善下载，并以 Legacy 风格轻前端切入
- **决策时间：** 2026-06-24
- **上下文：** 首批 CLI MVP 已通过真实样本验收；用户明确提出下载功能落地和完善优先级应高于下一批媒体处理功能，同时希望项目能边开发边使用，并保持 Legacy 前端布局与使用习惯。
- **决策：** Phase 3 先做下载工作流增强，再做贴近 Legacy 的本地轻前端；视频切片与资产扫描延后到下载体验稳定后评估。前端技术栈先参考 Legacy，若 Legacy 使用 Vite / React / TypeScript 或相近方案，v2 优先采用相近路线。
- **后果：** 项目更快进入真实日常使用；前端不会过早泛化成完整平台，但能保留老用户的空间记忆。需要先补充 `docs/UI_COMPAT.md` 并考古 Legacy 技术栈。
- **状态：** 已接受
