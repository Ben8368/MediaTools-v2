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
- **Legacy 来源：** 旧前端源码、截图、运行界面、用户熟悉的导航和任务布局。Legacy 技术栈已确认使用 Vite + React + TypeScript + Vitest；v2 采用同类轻前端路线，但只迁移壳层、空间关系和下载工作台体验，不迁移旧 API 耦合、AI/PS/AE、文件管理和 vendor/构建产物。
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
- **状态：** [客观已验证] - 已建立 `docs/UI_COMPAT.md` 与 `docs/UI_API_CONTRACT.md`；v2 `frontend/` 已初始化 Vite + React + TypeScript 下载工作台壳层，`python scripts/verify.py` 纳入 frontend `npm ci`、3 tests、build 并通过；npm audit 0 vulnerabilities。下一步需实现本地 API 适配层并进行用户主观 UI 验收。

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
- **状态：** [客观已验证] - macOS venv 中 `python scripts/verify.py` 通过：106 passed, 6 skipped；review 红灯修复后复验 125 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`

### Feature-015：下载安全边界与批量结果硬化 — Phase 3-A Safety
- **提交时间：** 2026-06-25
- **类型：** 安全硬化 / 下载工作流可靠性
- **描述：** 修复 review 红灯项：真实下载在语言探测前先校验 URL，避免非 http(s) URL 进入 `yt-dlp`；`--output-template` 禁止绝对路径和 `..` 片段，确保输出模板相对下载目录；并发下载结果按输入序号归档，重复 URL 不会互相覆盖；多语言字幕不再折叠为同一无语言后缀文件名。
- **用户价值：** 下载入口的文件写入边界更清晰，批量 summary 更可信，多语言字幕不会因自动重命名丢失或混淆。
- **前置依赖检查：**
  - 技术依赖：无新增运行时依赖；继续复用标准库、yt-dlp 和现有 mock 测试方式。
  - 环境依赖：真实下载仍依赖 PATH 中的 `yt-dlp`；安全校验本身不触网。
  - 安全影响：非 http(s) URL 不再触发语言探测；输出模板无法通过绝对路径或 `..` 写出下载目录。
  - 跨平台兼容性：同时拒绝 POSIX 绝对路径、Windows drive 绝对路径和反斜杠形式的 `..` 片段。
- **预计影响模块：**
  - 源码：`src/mediatools/core/fetch.py`、`src/mediatools/core/fetch_naming.py`、`src/mediatools/commands/fetch.py`。
  - 测试：`tests/test_fetch_security.py`、`tests/test_fetch_parallel.py`、`tests/test_fetch_naming.py`、`tests/test_cli.py`。
  - 文档：`README.md`、`03_Context.md`、`04_Features.md`、`05_Lessons.md`。
- **验收思路：**
  - 单元测试覆盖非法 URL 不调用 runner、路径逃逸模板拒绝、安全子目录模板允许、重复 URL 并发结果保留、多语言字幕保留后缀、CLI 默认 `-t mp4`。
  - 标准验证覆盖全量 pytest、ruff、doctor 和文件行数限制。
- **降级/回滚策略：** 如需保留多语言字幕旧折叠行为，可在后续新增显式参数；默认行为优先避免数据丢失。
- **状态：** [客观已验证] - macOS venv 中 `python scripts/verify.py` 通过：125 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`

### Feature-016：review 黄灯收敛 — Phase 3-A Maintenance
- **提交时间：** 2026-06-25
- **类型：** 维护性 / CLI 体验
- **描述：** 收敛 review 中可立即处理的黄灯项：CLI 错误输出接入项目自定义 `core.logging`；`fetch` CLI 增加 3600 秒默认下载超时并保留 `--timeout 0` 不限时；命令分发从多段 `if` 改为映射；`ProcessRunner` 从宽泛 `Callable[..., ...]` 改为明确 Protocol。
- **用户价值：** 长时间卡住的下载默认可被超时保护，CLI 分发和外部进程 runner 类型更易维护，自定义日志模块不再只是测试覆盖的孤岛。
- **前置依赖检查：**
  - 技术依赖：无新增运行时依赖。
  - 环境依赖：真实下载仍依赖 PATH 中的 `yt-dlp`；超时为 CLI 默认值，core API 仍允许调用方自行传入。
  - 安全影响：默认超时降低下载进程永久挂起风险；`--timeout 0` 保留用户对超长任务的显式控制。
  - 跨平台兼容性：仅使用标准库 argparse、Protocol 和现有日志封装。
- **预计影响模块：**
  - 源码：`src/mediatools/cli.py`、`src/mediatools/commands/fetch.py`、`src/mediatools/core/ffmpeg.py`。
  - 测试：`tests/test_cli.py`、现有 `tests/test_logging.py`、`tests/test_ffmpeg.py`。
  - 文档：`README.md`、`03_Context.md`、`04_Features.md`、`05_Lessons.md`。
- **验收思路：**
  - 单元测试覆盖默认 fetch timeout 和 `--timeout 0`。
  - 标准验证覆盖全量 pytest、ruff、doctor 和文件行数限制。
- **降级/回滚策略：** 如默认 3600 秒不适合真实大文件任务，可调整 CLI 默认或在前端下载工作台中暴露更明确的预设。
- **状态：** [客观已验证] - macOS venv 中 `python scripts/verify.py` 通过：127 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`；最新推送 CI 三平台绿灯

### Feature-017：完美绿灯维护收口 — Phase 3-A Perfect Green
- **提交时间：** 2026-06-25
- **类型：** 维护性 / 验证体验 / CI 硬化
- **描述：** 暂缓后续功能开发，专注消除剩余预警：将 `core/fetch.py` 的 cookie 参数构造与语言解析拆到独立模块；将 `tests/test_fetch.py` 中参数构造、语言解析测试拆到独立测试文件；所有 Python 文件降至 350 行预警线以下；CI 升级到 `actions/checkout@v7`、`actions/setup-python@v6`，并把 macOS runner 固定为 `macos-15`。
- **用户价值：** 代码职责更清晰，测试文件更容易维护，CI 输出减少平台迁移和 Node runtime 预警，后续进入轻前端前工程底座更干净。
- **前置依赖检查：**
  - 技术依赖：无新增运行时依赖；CI action tag 已通过远端 tag 查询确认存在。
  - 环境依赖：本地验证仍使用 macOS venv；CI 仍覆盖 ubuntu / windows / macOS。
  - 安全影响：不改变下载安全边界和用户可见下载行为。
  - 跨平台兼容性：CI macOS 从浮动 `macos-latest` 固定为 `macos-15`，避免近期 runner 迁移带来的不确定性。
- **预计影响模块：**
  - 源码：`src/mediatools/core/fetch.py`、`src/mediatools/core/fetch_auth.py`、`src/mediatools/core/fetch_resolution.py`。
  - 测试：`tests/test_fetch.py`、`tests/test_fetch_args.py`、`tests/test_fetch_resolution.py`。
  - CI：`.github/workflows/ci.yml`。
  - 文档：`03_Context.md`、`04_Features.md`、`05_Lessons.md`。
- **验收思路：**
  - 标准验证覆盖全量 pytest、ruff、doctor 和文件行数限制。
  - 推送后以 CI 三平台绿灯且无原先 Node/macOS migration annotation 作为跨平台验证。
- **降级/回滚策略：** 如新版 action major 在 GitHub runner 上出现兼容问题，可回退到已验证的上一 major，同时保留 `macos-15` 固定 runner。
- **状态：** [客观已验证] - macOS venv 中 `python scripts/verify.py` 通过：127 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`；最新推送 CI 三平台绿灯

### Feature-018：review 追补硬化 — Phase 3-A Reliability
- **提交时间：** 2026-06-25
- **类型：** 可靠性 / CLI 错误体验 / 下载后处理边界
- **描述：** 修复 review 追补项：字幕转换输入缺失、`fetch --input-file` 误传目录、`--summary-json` 写入失败等文件 I/O 异常统一转为 `MediaToolsError`/`MediaFileError`，避免 CLI 泄露 Python traceback；下载完成后的字幕语言后缀清理改为基于下载前后快照，只处理本次 yt-dlp 新增或变更的字幕文件，避免误改历史字幕；并发下载收到 `KeyboardInterrupt` 时取消未完成 future 并以 `shutdown(wait=False, cancel_futures=True)` 尽快返回 partial summary。
- **用户价值：** 用户输错路径或权限不足时看到稳定的一行错误；同一输出目录中的旧字幕不会被新下载任务误重命名；并发下载中断时更容易拿到可追踪的失败摘要。
- **前置依赖检查：**
  - 技术依赖：无新增运行时依赖；继续使用标准库、pytest、ruff。
  - 环境依赖：真实下载仍依赖 PATH 中的 `yt-dlp`；本次验证使用 mock 与 CLI dry-run 覆盖，不触发网络。
  - 安全影响：收紧文件 I/O 错误边界，不扩大下载目录写入范围。
  - 跨平台兼容性：路径与异常处理均使用 `pathlib`、标准异常和现有错误模型。
- **预计影响模块：**
  - 源码：`src/mediatools/core/subtitle.py`、`src/mediatools/core/fetch.py`、`src/mediatools/core/fetch_naming.py`、`src/mediatools/commands/fetch.py`。
  - 测试：`tests/test_subtitle.py`、`tests/test_fetch.py`、`tests/test_fetch_parallel.py`、`tests/test_cli.py`。
  - 文档：`03_Context.md`、`04_Features.md`、`05_Lessons.md`。
- **验收思路：**
  - CLI 回归测试覆盖缺失字幕、input-file 目录、summary-json 目录三类 traceback 风险。
  - 单元测试覆盖旧字幕不被本次下载后处理误改名，以及并发中断时 executor 非等待关闭。
  - 标准验证覆盖全量 pytest、ruff、doctor 和文件行数限制。
- **降级/回滚策略：** 如后续需要基于 yt-dlp 产物 manifest 做更精确后处理，可保留当前快照机制作为保守兜底；如并发中断仍需终止已运行子进程，再扩展 subprocess 层的进程终止能力。
- **状态：** [客观已验证] - Windows 中 `python scripts/verify.py` 通过：135 passed, 6 skipped；ruff 通过；doctor 发现 `ffmpeg`、`ffprobe`、`yt-dlp`

### Feature-019：字幕-only 生产样本打磨 — Phase 3-A Subtitle Workflow
- **提交时间：** 2026-06-25
- **类型：** 字幕下载体验 / 真实批量样本验证
- **描述：** 针对用户提供的 51 条 YouTube/Shorts 链接打磨字幕-only 工作流：`--subtitles-only` 在未显式指定字幕类型时默认同时尝试人工字幕和自动字幕，且不再传递无意义的视频格式预设；`--sub-langs original` 下载到 `*-orig` 与普通语言 fallback 时，优先保留最具体的 `*-orig` 原语言字幕并整理为干净 `.srt`；重复 URL 产生的同内容字幕会自动去重；同一输出目录的字幕后处理加锁，避免并发下载时的 rename 竞态；下载后对本次新增/变更的 SRT/VTT 执行 rolling caption 清理，去掉 YouTube 自动字幕中连续 cue 重复上一行的内容。
- **用户价值：** 用户只需一条命令即可批量下载原语言 SRT 字幕且不下载视频；生产目录中不会出现成对的 `.xx-orig.srt` / `.xx.srt` 或重复残留文件；批量重复链接也能保持输出目录干净。
- **前置依赖检查：**
  - 技术依赖：无新增运行时依赖；继续复用系统 `yt-dlp` 与 yt-dlp 内置 `--convert-subs srt`。
  - 环境依赖：真实批量验证依赖网络与 PATH 中的 `yt-dlp`；自动化测试仍使用 mock，不触网。
  - 安全影响：不扩大下载写入范围；继续只接受 http/https URL。
  - 跨平台兼容性：路径与文件比较使用 `pathlib` 和标准库；Windows 真实验证通过。
- **预计影响模块：**
  - 源码：`src/mediatools/core/fetch.py`、`src/mediatools/core/fetch_naming.py`、`src/mediatools/core/fetch_postprocess.py`。
  - 测试：`tests/test_fetch_args.py`、`tests/test_fetch.py`、`tests/test_fetch_naming.py`。
  - 文档：`README.md`、`03_Context.md`、`04_Features.md`、`05_Lessons.md`。
- **验收思路：**
  - 单元测试覆盖 `--subtitles-only` 默认字幕开关、不传 `-t mp4`、显式字幕类型选择、原语言优先清理、重复字幕内容去重。
  - 单元测试覆盖 rolling caption 行级重叠去重、短重复 cue 丢弃，以及 fetch 后处理自动清理本次下载字幕。
  - 真实样本验证覆盖 51 条 YouTube/Shorts 字幕-only 批量下载，目标为 `51 succeeded, 0 failed` 且仅输出 SRT。
  - 标准验证覆盖全量 pytest、ruff、doctor 和文件行数限制。
- **降级/回滚策略：** 若后续需要保留 fallback 字幕，可新增显式参数；默认行为继续优先“一个视频一个原语言 SRT”的干净生产目录。
- **状态：** [客观已验证] - Windows 中真实 51 URL 字幕-only 批量通过：51 succeeded, 0 failed，仅输出 51 个 SRT；rolling caption 内容去重后 `python scripts/verify.py` 通过：141 passed, 6 skipped；ruff 通过；doctor 发现 `ffmpeg`、`ffprobe`、`yt-dlp`

### Feature-020：字幕合并与并发控制收口 — Phase 3-A Subtitle Hardening
- **提交时间：** 2026-06-25
- **类型：** 可靠性 / 字幕可读性 / 下载并发控制
- **描述：** 在 review 后继续收敛字幕句子级合并和并发下载边界：同输出目录锁池使用引用计数避免等待线程期间创建第二把锁；字幕合并识别英文、CJK、阿语、天城体等多语言句界；长句按词时间边界切分，既保留原始结束时间，又避免可切分文本超过 `max_duration_ms`；`--max-concurrent` 非正数统一转为项目错误；配置文件 `max_concurrent_downloads` 仅作为上限。
- **用户价值：** 批量字幕-only 下载在并发场景下更稳定；自动字幕输出更适合阅读；错误输入给出明确提示，避免静默降级为串行。
- **前置依赖检查：**
  - 技术依赖：无新增运行时依赖，继续使用标准库。
  - 环境依赖：自动化测试使用 mock / 纯函数，不触发网络。
  - 安全影响：并发上限保护下载资源与站点访问压力；不扩大文件写入范围。
  - 跨平台兼容性：锁、路径和配置均使用标准库；需通过 CI 三平台复核。
- **预计影响模块：**
  - 源码：`src/mediatools/core/subtitle_merge.py`、`src/mediatools/core/fetch_postprocess.py`、`src/mediatools/core/config.py`、`src/mediatools/commands/fetch.py`。
  - 测试：`tests/test_subtitle_merge.py`、`tests/test_fetch_locks.py`、`tests/test_config.py`、`tests/test_cli.py`。
  - 文档：`README.md`、`03_Context.md`、`04_Features.md`、`05_Lessons.md`、`REFACTOR.md`。
- **验收思路：**
  - 单元测试覆盖锁池引用计数、多语言句界、长句按词切分、不截断尾部时长、非正并发数错误。
  - 标准验证覆盖全量 pytest、ruff、doctor 和文件行数限制。
- **降级/回滚策略：** 如按词切分对无空格语言仍不够理想，后续可增加字符级或语言特定分词策略；当前保守保持无词边界时不强切单字。
- **状态：** [客观已验证] - Windows 中 `python scripts/verify.py` 通过：160 passed, 6 skipped；ruff 通过；doctor 发现 `ffmpeg`、`ffprobe`、`yt-dlp`

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
| P3-A Safety | 下载安全边界与批量结果硬化 | P0 | 标准库 | URL 预校验、模板路径边界、重复 URL summary、多语言字幕保留 | Feature-015 |
| P3-A Maintenance | review 黄灯收敛 | P1 | 标准库 | CLI 日志接入、默认下载超时、命令分发映射、runner Protocol | Feature-016 |
| P3-A Perfect Green | 完美绿灯维护收口 | P1 | 标准库 / CI | 拆分预警文件、降低行数风险、升级 CI action 与固定 macOS runner | Feature-017 |
| P3-A Reliability | review 追补硬化 | P1 | 标准库 | 文件 I/O 统一项目错误、字幕后处理快照边界、并发中断快速收口 | Feature-018 |
| P3-A Subtitle Workflow | 字幕-only 生产样本打磨 | P0 | yt-dlp | 只下字幕、原语言 SRT、fallback 清理、重复字幕去重、rolling 内容清理、51 URL 真实验收 | Feature-019 |
| P3-A Subtitle Hardening | 字幕合并与并发控制收口 | P1 | 标准库 | 锁池引用计数、多语言句界、按词时间切分、并发参数校验 | Feature-020 |
| P3-B | Legacy 风格轻前端 / 下载工作台 | P1 | Vite / React / TypeScript | 壳层已启动，下一步接本地 API 适配层 | Feature-011 |
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
