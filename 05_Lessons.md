### H-001：仅以 03_Context 为准不足以防止文档漂移
- **假设：** 只要 `03_Context.md` 准确，其他治理文档可以滞后更新。
- **验证方式：** 评审时发现 `REFACTOR.md`、`04_Features.md` 与 `03_Context.md` 状态不一致，会误导接手者。
- **状态：** 已否决 — 变更时须同步 `03`、`01`、`REFACTOR`、`04`；见 `02_AI_Rules.md` §11。

### H-002：最小依赖可行性
- **假设：** 媒体工具可以只依赖系统 ffmpeg + 轻量图像库
- **验证方式：** 实现核心功能后评估依赖数量
- **状态：** 阶段性验证通过 — 首批 MVP 运行时依赖保持为空，媒体能力依赖系统 `ffmpeg` / `ffprobe` / `yt-dlp`。Phase 3 轻前端若引入 Node 工具链，必须作为前端开发依赖管理，不回流到 Python core 运行时。

### H-003：CLI 优先架构足够
- **假设：** 不需要 Web UI，CLI + 脚本集成即可满足需求
- **验证方式：** 用户反馈；实际使用场景
- **状态：** 部分否决 — CLI 足以验证核心媒体能力，但下载落地、批量任务和结果查看需要轻前端来降低日常使用成本。Phase 3 进入 Legacy 风格本地轻前端评估。

### L-001：忽略规则验证以 `git ls-files --others --exclude-standard` 为准
- **时间：** 2026-06-24 11:55:05 +08:00
- **背景：** 工作区存在 Legacy 残留、运行产物和构建缓存，普通 `git status` 输出可能受命令执行时机影响。
- **经验：** 修改 `.gitignore` 后，使用 `git status --short --branch` 查看预期修改文件，再用 `git ls-files --others --exclude-standard` 确认是否仍有未被忽略的未跟踪文件。
- **状态：** 已采纳

### L-002：支持 `python -m package` 需要 `__main__.py`
- **时间：** 2026-06-24 12:10:01 +08:00
- **背景：** 最小 CLI 初版只配置了 console script，导致 `python -m mediatools` 报 `No module named mediatools.__main__`。
- **经验：** README 中若提供 `python -m package` 命令，必须添加 `src/<package>/__main__.py` 并用测试覆盖模块执行入口。
- **状态：** 已采纳

### L-003：极小入口文件可用 per-file ignore 精准豁免 ruff I001
- **时间：** 2026-06-24 12:10:01 +08:00
- **背景：** `src/mediatools/__main__.py` 仅包含入口胶水导入，但 ruff 在本机环境持续报 `I001`。
- **经验：** 保留全局 import 排序规则，只对入口胶水文件使用 `[tool.ruff.lint.per-file-ignores]` 精准豁免，避免为低价值格式问题牺牲整体质量门。
- **状态：** 已采纳

### L-004：路径逻辑放 core 层并配套 tmp_path 测试
- **时间：** 2026-06-24 12:52:17 +08:00
- **背景：** Phase 1 启动跨平台路径模块，需避免在 CLI 层硬编码路径拼接。
- **经验：** 路径工具放 `src/mediatools/core/paths.py`，测试用 `pytest` 的 `tmp_path` fixture，不依赖本机目录；用户输入写入前用 `is_safe_child()` 防目录穿越。
- **状态：** 已采纳

### L-005：Windows 用户级安装时 console script 可能不在 PATH
- **时间：** 2026-06-24 12:57:11 +08:00
- **背景：** `pip install -e ".[dev]"` 在不可写系统 site-packages 时走用户安装，`mediatools.exe` 落到 `Roaming\Python\Python314\Scripts`，若未加入 PATH 会告警。
- **经验：** README 优先推荐 `python -m mediatools`；文档与测试覆盖模块入口，不依赖 console script 是否在 PATH。
- **状态：** 已采纳

### L-006：客观验证由 AI 执行，用户只验主观体验
- **时间：** 2026-06-24 13:05:00 +08:00
- **背景：** AI 开发项目若要求用户重复跑 pytest/ruff/doctor，与 AI 自行执行等价，徒增往返。
- **经验：** 统一入口 `python scripts/verify.py`（安装、测试、lint、doctor、ffmpeg/PATH 报告）；AI 本地跑 + CI 矩阵绿 → 直接打钩；用户只评「好不好用」和 MVP 等业务决策。
- **状态：** 已采纳

### L-007：外部媒体工具封装与测试解耦
- **时间：** 2026-06-24 14:15:03 +08:00
- **背景：** 首批 MVP 依赖 ffmpeg / ffprobe / yt-dlp，但单元测试若真实调用这些工具会受本机 PATH、媒体样本和网络状态影响。
- **经验：** 将外部工具调用集中到 `core/ffmpeg.py`，所有调用都用参数列表并禁止 `shell=True`；功能模块只构造参数和解析结果，测试通过 mock `shutil.which()` 与 runner 覆盖成功/失败路径，不依赖真实媒体或网络。
- **状态：** 已采纳

### L-008：前后端分离不是问题，过早分离才是问题
- **时间：** 2026-06-24 14:30:25 +08:00
- **背景：** 评审治理文档时发现“前后端分离架构 → 单体 CLI 优先”的表述容易被误读为否定前后端分离本身。
- **经验：** 当前阶段继续 CLI 优先，但 core 与适配层必须保持解耦；只有当真实媒体工作流、输入输出契约、错误模型和任务进度模型稳定后，才评估 Web UI / 桌面 GUI / API 层。
- **状态：** 已采纳

### L-009：500 行规则要制度化，不能只靠口头提醒
- **时间：** 2026-06-24 14:30:25 +08:00
- **背景：** 用户明确提出单文件不超过 500 行的治理诉求，但原治理文件未写入硬性阈值。
- **经验：** 350 行预警、450 行评估拆分、500 行默认禁止继续堆业务逻辑；拆分按 core / command / adapter / fixture 等真实职责边界进行，避免为行数制造空壳抽象。
- **状态：** 已采纳

### L-010：verify 安装阶段可能受用户级 site-packages 权限影响
- **时间：** 2026-06-24 14:34:30 +08:00
- **背景：** 文档优化后复跑 `python scripts/verify.py`，普通权限在安装 `ruff` 到用户级 `site-packages` 时遇到 `Permission denied`，提升权限后验证通过。
- **经验：** 若 `verify.py` 失败点在 pip 安装且错误指向用户级 Python 目录权限，先判定为环境权限问题；重跑验证或修复本机 Python 权限后，再判断代码/文档变更是否失败。
- **状态：** 已采纳

### L-011：本地 smoke 能补足 mock 测试，但不能替代主观验收
- **时间：** 2026-06-24 14:41:12 +08:00
- **背景：** Phase 2 收口时，mock 单测已覆盖外部工具封装，但仍需要确认真实文件 I/O 链路能跑通。
- **经验：** 用 ffmpeg 生成小型测试媒体，再通过 CLI 覆盖 `probe`、`subtitle convert`、`encode`、`screenshot`，可以作为客观收口；`fetch` 和真实媒体体验仍受网络、站点、素材复杂度和用户预期影响，不能用 smoke 直接标 `[已完成]`。
- **状态：** 已采纳

### L-012：YouTube 自动字幕需要显式参数
- **时间：** 2026-06-24 15:11:05 +08:00
- **背景：** 真实 YouTube 链接验收时，`--write-subs` 能下载视频但没有字幕；`yt-dlp --list-subs` 显示该视频只有 automatic captions。
- **经验：** `--write-subs` 只覆盖人工字幕，自动字幕需单独传 `--write-auto-subs`。下载类功能的真实体验验收要区分人工字幕、自动字幕和站点可用性。
- **状态：** 已采纳

### L-013：清理项目目录时归档未知本地数据
- **时间：** 2026-06-24 15:11:05 +08:00
- **背景：** `data/tasks.db` 是旧本地 SQLite 任务库，当前 v2 代码无引用，但其中仍有历史任务记录。
- **经验：** 对无引用但可能含历史数据的本地文件，不直接删除；先归档到 `data/legacy/`。明确生成物（`.tmp-tests`、缓存、coverage、重复下载）可以清理。
- **状态：** 已采纳

### L-014：`.agents/` 为空不是健康问题
- **时间：** 2026-06-24 16:49:42 +08:00
- **背景：** 项目根目录存在 `.agents/`，但当前为空；治理入口实际是根目录 `AGENTS.md` 与 `01`-`05` 文档。
- **经验：** `.agents/` 可作为未来多 AI 工具专属补充规则目录，但为空时不影响项目健康。除非出现工具专属规则、模板或交接文件需求，否则不要为了“看起来完整”强行填充。
- **状态：** 已采纳

### L-015：前端重构要保留 Legacy 用户的空间记忆
- **时间：** 2026-06-24 16:49:42 +08:00
- **背景：** 用户明确希望轻前端贴近 Legacy，开发维护要容易，并方便后续快速恢复之前的前端 UI 样式；前端技术可以变化，但排版布局应保持一致。
- **经验：** 前端实现前先建立 Legacy UI 兼容基线，记录技术栈、导航、工作区、任务列表、结果区、视觉密度和下载流程。技术栈选型优先贴近 Legacy；业务逻辑仍留在 Python core / CLI / API 适配层，前端只做任务提交和状态呈现。
- **状态：** 已采纳

### L-016：500 行拆分要求必须进入验证入口
- **时间：** 2026-06-24 17:03:14 +08:00
- **背景：** 用户要求单文件超过 500 行必须作为硬性拆分要求，而不是仅靠治理文档提醒。
- **经验：** 将 Python 文件行数检查放入 `scripts/verify.py`，覆盖 `src/`、`tests/`、`scripts/`。超过 500 行直接失败，开发者必须先按真实职责边界拆分再继续。
- **状态：** 已采纳

### L-017：yt-dlp `-t mp4` 预设已覆盖 H264+AAC+MP4，无需额外转码步骤
- **时间：** 2026-06-24 21:50:00 +08:00
- **背景：** 用户提出下载视频后需要 H264+AAC+MP4 格式；初步计划是先下载再用 `mediatools encode` 重编码。
- **经验：** yt-dlp 的 `-t mp4`（或 `--preset-alias mp4`）等同于 `--merge-output-format mp4 --remux-video mp4 -S vcodec:h264,...,acodec:aac`，已能优先选择 H264+AAC 流并封装为 MP4。只需在 `fetch` 中暴露 `--preset` 参数即可，无需额外调用 ffmpeg。
- **状态：** 已采纳

### L-018：yt-dlp 无原语言关键字，需先探测 `--print language` 字段
- **时间：** 2026-06-24 21:50:00 +08:00
- **背景：** 用户要求只下载视频原语言字幕；yt-dlp `--sub-langs` 只支持 `all` 和语言代码，无 `original` 或 `default` 关键字。
- **经验：** 实测发现 yt-dlp 的 `--print language` 字段（如 `en-US`、`pt-BR`）可靠；自动字幕中带有 `<lang>-orig` 后缀（如 `en-orig`）才是原语言字幕，其他语言都是机器翻译。在 `fetch.py` 中实现 `_resolve_sub_langs()` 函数，把 `--sub-langs original` 在运行时替换为 `yt-dlp --print language` 的探测结果，失败时降级为 `all`。
- **状态：** 已采纳

### L-019：`--convert-subs` 是 yt-dlp 原生参数，可直接透传
- **时间：** 2026-06-24 21:50:00 +08:00
- **背景：** 用户要求字幕保存为 SRT 格式；yt-dlp 默认下载 VTT 格式（YouTube 原生格式）。
- **经验：** yt-dlp 的 `--convert-subs srt` 会在下载后自动将 VTT 转为 SRT，支持 `srt/vtt/ass/lrc`；这是内置后处理能力，无需额外调用 `mediatools subtitle convert`。在 `fetch` 中直接透传 `--convert-subs` 参数即可。
- **状态：** 已采纳

### L-020：`subprocess.run(encoding="utf-8")` 在 Windows 上会崩溃
- **时间：** 2026-06-25 01:30:00 +08:00
- **背景：** 批量真实下载验收时，yt-dlp 在 Windows 上输出土耳其语、葡萄牙语等非 ASCII 字符时抛出 `UnicodeDecodeError`，导致后续 URL 全部跳过。
- **经验：** Windows 控制台默认代码页（CP936 / CP850）与 `encoding="utf-8"` 不匹配；必须在 `subprocess.run` 中加 `errors="replace"`，以 Unicode 替换字符兜底非 UTF-8 字节。已在 `run_tool` (core/ffmpeg.py) 加入。
- **状态：** 已采纳

### L-021：`--write-subs` 与 `--write-auto-subs` 同时使用会重复追加 `--sub-langs`
- **时间：** 2026-06-25 01:30:00 +08:00
- **背景：** `build_fetch_args` 中 `if write_subtitles` 和 `if write_auto_subtitles` 两个独立分支各自追加 `--sub-langs`，导致参数重复（功能正确但冗余）。
- **经验：** 当两个条件共用同一参数时，让第二个条件只在第一个未设时才追加该参数；或在构建参数时收集一次去重再统一 append。
- **状态：** 已采纳

### L-022：yt-dlp `--print language` 返回带 locale 的代码，但字幕标签不含 locale
- **时间：** 2026-06-25 01:30:00 +08:00
- **背景：** `--print language` 返回 `pt-BR`、`en-US` 等带 locale 的 ISO 代码，但 YouTube 自动字幕的 base 标签是 `pt-orig`/`pt`、`en-orig`/`en`（不含 locale），导致 `--sub-langs pt-BR-orig` 不匹配任何字幕。
- **经验：** `_resolve_sub_langs` 在探测到 `-` 分隔的 locale 代码时（如 `pt-BR`），同时生成 `pt-BR-orig,pt-BR,pt-orig,pt`，覆盖带 locale 和不带 locale 的两种标签；探测结果不含 `-` 时（如 `ar`），保持 `<lang>-orig,<lang>` 即可。
- **状态：** 已采纳

### L-023：YouTube playlist 可能需要显式登录态
- **时间：** 2026-06-24 22:05:43 +08:00
- **背景：** macOS 上校验单条 YouTube playlist 链接时，`yt-dlp --flat-playlist` 能识别 11 条视频，但实际提取每个视频都返回 `Sign in to confirm you’re not a bot`。此前 Win11 单/批量链接未触发该风控。
- **经验：** 这类阻断不是 macOS 或 ffmpeg 兼容性问题，而是 YouTube 对当前网络、会话、playlist 批量提取或请求指纹触发登录/反机器人确认。下载工具应显式暴露 `--cookies-from-browser` 和 `--cookies`，但不能默认读取浏览器登录态；两种 cookie 来源应互斥。`--sub-langs original` 的语言探测也必须透传同一 cookie 来源，且 playlist 场景下 `--print language` 可能返回多行，应取第一条有效语言。本轮用 `--cookies-from-browser chrome` 复测后，前三条 playlist 视频已成功下载并经 ffprobe 验证为 H264 + AAC + MP4；中途 Ctrl-C 会导致 `summary.json` 未写出并留下当前条目的 `.part` 临时文件。
- **状态：** 已采纳

### L-024：macOS 验证入口必须避开系统 Python 与 Homebrew 全局 pip
- **时间：** 2026-06-25 00:30:46 +08:00
- **背景：** `python scripts/verify.py` 在 macOS shell 中可能找不到 `python`；`python3` 常命中 Apple Command Line Tools Python 3.9，不满足项目 Python 3.11+；Homebrew Python 又会因 PEP 668 阻止直接向全局环境 `pip install -e .[dev]`。
- **经验：** macOS 本地验证应使用 Homebrew/pyenv 的 Python 3.11+ 创建虚拟环境后运行 `python scripts/verify.py`。`verify.py` 应先检查 Python 版本，安装失败遇到 `externally-managed-environment` 时明确提示创建 venv，而不是让用户误判为项目代码失败。
- **状态：** 已采纳

### L-025：dry-run 不应触发网络探测或读取浏览器登录态
- **时间：** 2026-06-25 00:30:46 +08:00
- **背景：** `fetch --dry-run --sub-langs original` 原先会先调用 `yt-dlp --print language` 解析原语言；若同时传 `--cookies-from-browser`，dry-run 也可能读取浏览器 cookie。
- **经验：** dry-run 的承诺是只构造计划，不做网络访问和登录态读取。`original` 这类运行时探测值应在真实下载时解析；dry-run 中保留原始参数即可。
- **状态：** 已采纳

### L-026：批量下载中断也要写出可追踪摘要
- **时间：** 2026-06-25 00:30:46 +08:00
- **背景：** playlist 下载中途 Ctrl-C 会留下 `.part` 临时文件，并且如果异常直接冒泡，CLI 没机会写出 `summary.json`。
- **经验：** 批量任务应捕获 `KeyboardInterrupt`，把当前 URL 记录为失败/中断项后停止批次，让 CLI 能输出 partial summary。不要自动删除 `.part`，因为用户可能需要恢复或检查 yt-dlp 的半成品。
- **状态：** 已采纳

### L-027：macOS 默认目录应使用 `~/Library`
- **时间：** 2026-06-25 00:30:46 +08:00
- **背景：** 早期配置模块把 macOS 与 Linux 一起归到 XDG 默认路径（`~/.config`、`~/.cache`、`~/.local/share`），可运行但不符合 macOS 桌面应用习惯。
- **经验：** macOS 无显式 XDG 环境变量时，默认配置/数据放 `~/Library/Application Support/mediatools`，缓存放 `~/Library/Caches/mediatools`；同时继续允许 XDG 环境变量覆盖，方便高级用户和 CI。
- **状态：** 已采纳

### L-028：友好命名模板应编译到 yt-dlp 原生模板
- **时间：** 2026-06-25 00:38:41 +08:00
- **背景：** 用户需要按 `KR-作者名字-标题名-平台名.mp4` 这类结构命名下载视频，但直接暴露 yt-dlp 的 `%(title)s` 语法对日常使用不够直观。
- **经验：** 保留高级 `--output-template`，同时新增白名单式友好模板（如 `{lang}-{author}-{title}-{platform}.{ext}`）并编译为 yt-dlp 原生输出模板。默认语言码可复用 `yt-dlp --print language` 自动探测并映射为短码，dry-run 不能触网，应用 `AUTO` 占位预览；作者/标题来自平台元数据，需默认传递 `--windows-filenames` 让 yt-dlp 处理本地不可用文件名字符。
- **状态：** 已采纳

### L-029：下载 URL 校验必须早于任何外部探测
- **时间：** 2026-06-25 05:00:42 +08:00
- **背景：** review 发现真实下载会先调用 `yt-dlp --print language` 探测语言，再由下载参数构建阶段校验 URL；非 http(s) URL 因此可能先进入外部工具。
- **经验：** 网络下载入口的 URL scheme 校验必须放在最外层执行路径，包括 dry-run、语言探测、真实下载和失败摘要生成。异常处理里的“展示命令”也不能再次调用可能失败的参数构建逻辑。
- **状态：** 已采纳

### L-030：输出模板是路径边界的一部分
- **时间：** 2026-06-25 05:00:42 +08:00
- **背景：** `--output-template` 虽然会清洗字符，但仍允许内部 `../`，可能让 yt-dlp 写出指定输出目录。
- **经验：** 下载工具不能只校验输出目录，还要校验会参与路径拼接的模板。原生模板必须拒绝绝对路径、Windows drive 绝对路径和 `..` 片段；允许安全的相对子目录模板。多语言字幕重命名也应优先避免数据丢失：单语言可去后缀，多语言保留语言标记。
- **状态：** 已采纳

### L-031：下载超时默认值要保护普通用户，同时保留显式不限时
- **时间：** 2026-06-25 05:05:40 +08:00
- **背景：** review 指出 `yt-dlp` 默认无超时可能在网络异常时永久挂起；但真实长视频、playlist 或限速网络又可能超过普通短超时。
- **经验：** CLI 层应给交互用户一个保守的大默认超时（当前 3600 秒），避免无响应任务无限挂起；core 层继续接受调用方传入 timeout，CLI 用 `--timeout 0` 表示显式不限时，保留长任务逃生口。
- **状态：** 已采纳

### L-032：完美绿灯阶段要处理预警线和 CI annotation
- **时间：** 2026-06-25 05:13:33 +08:00
- **背景：** `verify.py` 的 500 行硬限制已通过，但 `core/fetch.py` 超过 350 行预警线、`tests/test_fetch.py` 接近 500 行评估线；CI 虽绿，但 GitHub Actions 仍提示 Node runtime 与 macOS runner 迁移 annotation。
- **经验：** “绿灯完美”不仅是测试通过，还要消除会误导后续接手者的维护预警。大文件应按真实职责拆分，而不是为了行数制造空壳；CI annotation 若可通过稳定 action 版本和固定 runner 消除，也应在进入下一阶段前收口。
- **状态：** 已采纳

### L-033：CLI 文件 I/O 必须转为项目错误
- **时间：** 2026-06-25 10:03:41 +08:00
- **背景：** review 追补发现 `subtitle convert` 输入文件不存在、`fetch --input-file` 误传目录、`--summary-json` 写入目录时会冒出 Python traceback，违反 CLI 层统一错误体验。
- **经验：** 任何用户输入路径触发的 `read_text`、`write_text`、`mkdir` 等 I/O 操作，都应先做存在性/文件类型检查，并把 `OSError` 转为 `MediaToolsError` 或更具体的 `MediaFileError`。CLI 回归测试不仅要断言错误消息，还要断言 stderr 不包含 `Traceback`。
- **状态：** 已采纳

### L-034：下载后处理不能默认扫描整个输出目录
- **时间：** 2026-06-25 10:03:41 +08:00
- **背景：** 字幕语言后缀清理原先在每次下载后扫描整个输出目录，可能把历史字幕文件也顺手重命名；并发下载时还可能扩大竞争窗口。
- **经验：** 下载后处理应尽量限制在本次任务产物范围内。若外部工具暂时没有稳定 manifest，可在调用前后记录目标目录中相关文件的快照，只处理新增或发生变化的候选文件；未来若引入 yt-dlp 产物清单，可再替换为更精确的 manifest 驱动。
- **状态：** 已采纳

### L-035：字幕-only 应默认产出一个干净原语言 SRT
- **时间：** 2026-06-25 10:46:30 +08:00
- **背景：** 用户提供 51 条 YouTube/Shorts 链接做真实生产样本。第一轮批量字幕-only 下载暴露两个体验问题：`--sub-langs original` 为了 fallback 会同时下载 `xx-orig` 与 `xx` 两份字幕；重复 URL 会留下额外 `*-orig.srt`；同一输出目录并发后处理还可能产生 rename 竞态。
- **经验：** 字幕-only 场景的默认目标应是“一个输入视频对应一个原语言 SRT”。`--subtitles-only` 未指定字幕类型时应默认尝试人工+自动字幕；字幕-only 不需要传视频格式预设；当 `*-orig` 与 fallback 同时存在时，优先保留最具体的 `*-orig` 并清理 fallback，再去除语言后缀；若目标已存在且内容相同，应删除重复文件而不是保留噪音。对同一输出目录的字幕后处理需要加锁，避免并发 rename 竞态。
- **状态：** 已采纳

### L-036：YouTube 自动字幕可能是 rolling/cumulative cue
- **时间：** 2026-06-25 11:03:26 +08:00
- **背景：** 用户检查 `.tmp-tests` 中下载到的 SRT，发现字幕内容并非只有文件重复，而是相邻 cue 内部会重复上一条的文本，例如 `A`、短暂 `A`、再到 `A / B`、短暂 `B`。这是 YouTube 自动字幕常见的滚动窗口输出，直接保存会让文本阅读体验很差。
- **经验：** 字幕清理要区分文件级去重和内容级去重。下载后处理应只处理本次新增/变更的 SRT/VTT，并在解析为 cue 后移除连续 cue 的行级前后重叠；纯重复短 cue 应丢弃并重新编号。对 ASS/LRC 等未解析格式保持只读跳过，避免误改未知格式。
- **状态：** 已采纳

### L-037：字幕长句合并要按时间词片切分
- **时间：** 2026-06-25 15:13:22 +08:00
- **背景：** 句子级字幕合并初版先把整句压成最多两行，再按行数切 duration。review 发现 15 秒长句会被修成不截尾但最后一个 cue 可能超过 `max_duration_ms`，导致阅读节奏和字幕显示时长不可控。
- **经验：** 字幕分块的基本单位应尽量保留时间信息。对有空格词边界的语言，先根据原 cue 时长估算每个词的起止时间，再按词片贪心切块；这样可同时保留原始 `end_ms`，并在词边界允许时保证每块不超过 `max_duration_ms`。对 CJK 等无空格文本，暂不强行单字切分，后续如有真实样本再增加语言特定策略。
- **状态：** 已采纳

### L-038：Legacy UI 适合壳层移植，不适合整包回流
- **时间：** 2026-06-25 17:13:24 +08:00
- **背景：** 评估是否把 Legacy UI 整体同步回来再精简，还是重新写前端。Legacy 前端保留了用户熟悉的桌面式左侧导航、窗口工作区、右侧面板和下载工作台，但也混有旧 API、AI/PS/AE、文件管理、vendor/构建产物等 v2 当前不应继承的复杂度。
- **经验：** 最优路线是“Legacy UI 壳层移植 + v2 业务逻辑重接”：沿用 Vite + React + TypeScript 的技术路线和空间关系，优先恢复下载工作台的视觉密度与操作路径；旧 API 调用、重型功能和平台耦合不直接迁移。前端验证应纳入 `scripts/verify.py`，但 Node 工具链只作为前端开发依赖，不回流到 Python core 运行时。
- **状态：** 已采纳

### L-039：Python stdlib HTTP server 足够支撑轻前端 API 适配层
- **时间：** 2026-06-25 18:00:00 +08:00
- **背景：** 实现下载工作台的本地 API 适配层，需要 HTTP 服务器暴露 doctor、fetch plan、fetch task 和任务列表接口。评估方案时有 `flask`/`fastapi` 等第三方选项。
- **经验：** `http.server.HTTPServer` + `ThreadingMixIn` + `BaseHTTPRequestHandler` 组合足以支撑轻前端 API 需求，无需引入 Web 框架。关键决策点：① 不依赖 `pip install` 任何新包；② 任务存储用内存 dict + `threading.Lock` 满足当前串行/低并发场景；③ `Vite dev server` 的 proxy 自动处理 CORS，无需在 Python 层加 CORS 头。后续若需要 WebSocket 推送、鉴权或持久化任务记录，再评估是否需要框架。
- **状态：** 已采纳

### L-040：API 任务模型增长时应拆出存储模块
- **时间：** 2026-06-25 21:44:13 +08:00
- **背景：** 为轻前端补齐任务持久化、时间戳、取消/删除/清空接口时，若继续把 `Task`/`TaskStore` 堆在 `api_server.py`，会触发 `scripts/verify.py` 的 500 行硬限制。
- **经验：** API server 只保留路由、请求解析和调度；任务记录、持久化、状态变更放在独立 `api_tasks.py`。这样既满足行数治理，也为后续硬取消 subprocess、任务历史查询、SQLite 迁移预留自然边界。
- **状态：** 已采纳

### L-041：本机权限异常时可把验证缓存指向工作区临时目录
- **时间：** 2026-06-25 21:44:13 +08:00
- **背景：** Windows 本机的用户级 Python site-packages、pytest temp、npm cache 目录可能出现权限拒绝，导致 `python scripts/verify.py` 在安装或 `npm ci` 阶段失败，而代码测试本身无误。
- **经验：** 先判断失败是否指向用户目录权限；若是，可临时设置 `PYTHONUSERBASE`、`PYTEST_ADDOPTS=--basetemp ...`、`npm_config_cache` 到仓库忽略的临时目录后复跑标准验证。不要把这类环境问题误判为代码回归。
- **状态：** 已采纳

### L-042：统一启动脚本要传递端口契约而不是修改配置文件
- **时间：** 2026-06-25 23:02:04 +08:00
- **背景：** 轻前端需要同时启动 Python API 与 Vite dev server。若用户改 API 端口，手动修改 `vite.config` 容易造成文档、配置和实际启动状态漂移。
- **经验：** 跨平台本地启动优先用 Python 脚本编排进程：用 `sys.executable` 启动 API，用 `npm run dev -- --host --port` 启动前端，并通过环境变量（当前 `VITE_MEDIATOOLS_API_TARGET`）把 API 地址传给 Vite proxy。这样 Windows/macOS/Linux 共用一条命令，且端口契约集中在启动入口。
- **状态：** 已采纳

### L-043：前端规模门禁需要隔离历史大文件
- **时间：** 2026-06-25 23:02:04 +08:00
- **背景：** 500 行硬限制最初只检查 Python，Legacy 前端迁入后出现多个超大 TSX/CSS 文件，导致治理规则对前端失效。
- **经验：** `scripts/verify.py` 应覆盖前端 `src/` 下 TS/TSX/CSS 源码。历史迁移大文件若暂时无法一次性拆分，必须显式列入隔离清单并在验证输出中报告，防止新增文件继续绕过门禁；后续应逐步拆分或移出主源码路径。
- **状态：** 已采纳
