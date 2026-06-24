### H-001：仅以 03_Context 为准不足以防止文档漂移
- **假设：** 只要 `03_Context.md` 准确，其他治理文档可以滞后更新。
- **验证方式：** 评审时发现 `REFACTOR.md`、`04_Features.md` 与 `03_Context.md` 状态不一致，会误导接手者。
- **状态：** 已否决 — 变更时须同步 `03`、`01`、`REFACTOR`、`04`；见 `02_AI_Rules.md` §11。

### H-002：最小依赖可行性
- **假设：** 媒体工具可以只依赖系统 ffmpeg + 轻量图像库
- **验证方式：** 实现核心功能后评估依赖数量
- **状态：** 待验证

### H-003：CLI 优先架构足够
- **假设：** 不需要 Web UI，CLI + 脚本集成即可满足需求
- **验证方式：** 用户反馈；实际使用场景
- **状态：** 待验证

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
