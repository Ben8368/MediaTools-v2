# Current Context

## 1. 项目状态快照

> **更新时间：** 2026-06-25 10:03:41 +08:00
> **当前分支：** refactor-v2
> **当前阶段：** Phase 3 - 下载工作流已验收，review 追补硬化已本地验证，继续转入 Legacy UI 兼容基线
> **验证状态：** 真实 7 URL 批量下载验收通过（H264+AAC+MP4 + SRT 原语言字幕）；macOS Chrome 登录态 playlist 校验前三条下载通过（H264+AAC+MP4，1080p）；review 完美绿灯收口后 macOS venv 标准验证通过（127 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`）；review 追补硬化后 Windows 标准验证通过（135 passed, 6 skipped；ruff 通过；doctor 发现 `ffmpeg`、`ffprobe`、`yt-dlp`）；上次推送 CI 三平台绿灯

## 2. 本轮阻断项

- [x] 同步治理文档状态（REFACTOR、04、01）
- [x] 补强 `02_AI_Rules.md`
- [x] 实现 `core/paths` 跨平台路径模块
- [x] 添加 GitHub Actions CI 工作流
- [x] 用户验证路径模块与 CI（本地 9 passed + ruff；CI #28076101163 三平台绿灯）
- [x] 实现核心架构三大模块（日志、错误处理、配置）
- [x] 推送核心架构代码并验证 CI 通过（CI #28077072580 三平台绿灯）

## 3. 技术栈决策状态

> **决策状态：** 已确认 Python CLI 优先

### 已确认项
1. **主语言选择**：Python 3.11+
2. **交互形态**：CLI 优先
3. **CLI 框架**：标准库 `argparse` 起步
4. **测试框架**：`pytest`
5. **依赖管理**：`pyproject.toml`
6. **分发方式**：Phase 1 先源码/可编辑安装，后续再评估 pipx 或单文件打包

### 决策依据
- 团队熟悉度
- 跨平台支持度
- 媒体处理生态成熟度
- 打包和部署复杂度
- 与 ffmpeg、yt-dlp 等外部工具的集成方式

### 当前演进项
- Web UI / 桌面 GUI 不再作为笼统暂缓项；Phase 3 先评估贴近 Legacy 的本地轻前端，用于边开发边使用。
- 单文件可执行程序分发推迟到发布准备阶段评估。

## 4. 知识库关联

> **Legacy 版本：** https://github.com/Ben8368/MediaTools  
> **新仓库：** https://github.com/Ben8368/MediaTools-v2  
> **当前分支：** refactor-v2

### 关键决策
- ✅ 采用治理文件体系（参考 weibo-workflow）
- ✅ 全新 orphan 分支重构，不保留历史包袱
- ✅ 技术栈采用 Python CLI 优先
- ✅ 核心功能清单已确认（首批 MVP A/B/C/D/E）
- ✅ 工程脚手架已通过验证
- ✅ `core/paths` 与 CI 已通过验证
- ✅ 前后端策略已澄清：不否定分离；Phase 3 轻前端必须贴近 Legacy 布局和用户路径，业务逻辑仍保留在 core / CLI / API 适配层

## 5. 当前任务焦点

- [x] 建立治理文档入口（01-05 + AGENTS.md）
- [x] 完成技术栈决策访谈
- [x] 验证 Python CLI 最小脚手架
- [x] 同步文档状态、补强 AI 规则
- [x] 实现跨平台路径模块（`src/mediatools/core/paths.py`）
- [x] 添加 CI 工作流（`.github/workflows/ci.yml`）
- [x] 用户验证路径模块与 CI
- [x] 实现核心架构模块：
  - [x] 日志系统（`src/mediatools/core/logging.py`）
  - [x] 错误处理体系（`src/mediatools/core/errors.py`）
  - [x] 配置加载与工作区约定（`src/mediatools/core/config.py`）
- [x] 推送并验证 CI 三平台绿灯（CI #28077072580）
- [x] 从 Legacy 版本提取核心功能清单（Feature-005~009，Tier 矩阵见 04 §3）
- [x] 用户确认首批 MVP = A/B/C/D/E（probe / 转码 / 字幕转换 / 截图 / 下载）
- [x] 实现首批 MVP（A→C→B→D→E）
- [x] 扩展 `doctor` 与 `scripts/verify.py` 外部工具报告（ffmpeg / ffprobe / yt-dlp）
- [x] 本地客观验证通过：53 passed, 6 skipped；ruff 通过
- [x] 补强治理规则：500 行阈值、前后端分离边界、客观/主观状态拆分
- [x] 治理文档优化后复跑 `python scripts/verify.py` 通过：53 passed, 6 skipped；ruff 通过；doctor 通过
- [x] 本地端到端 smoke 通过：生成 2 秒 MP4，覆盖 `probe` / `subtitle convert` / `encode` / `screenshot`
- [x] Phase 2 客观收口后最终复验通过：53 passed, 6 skipped；ruff 通过；doctor 通过
- [x] 推送后验证 CI 三平台绿灯（windows-latest / macos-latest / ubuntu-latest）
- [x] 用户委托真实样本体验验收：真实视频 probe/screenshot/encode/audio、真实字幕转换、YouTube fetch + 自动字幕下载均通过
- [x] 清理项目目录：移除临时 smoke/caches/coverage/重复下载；归档旧 `data/tasks.db` 到 `data/legacy/tasks.db`
- [x] 将单个 Python 文件超过 500 行设为 `scripts/verify.py` 硬性失败
- [x] 启动下载工作流增强：批量 URL 输入、dry-run、summary JSON、info JSON、download archive
- [x] 下载增强局部验证通过：`tests/test_fetch.py tests/test_cli.py` 共 18 passed，ruff 通过
- [x] 下载增强标准验证通过：`python scripts/verify.py`（500 行硬限制检查通过；63 passed, 6 skipped；ruff 通过；doctor 通过）
- [x] 实现 Feature-012（下载格式控制与原语言探测）：`--preset`、`--merge-format`、`--remux-video`、`--convert-subs`、`--format-sort`、`--sub-langs original` 自动探测原语言
- [x] 格式控制与原语言探测客观验证通过：73 passed, 6 skipped；ruff 通过；doctor 通过
- [x] 真实 7 URL 批量下载体验验收通过：H264+AAC+MP4 + SRT 原语言字幕（tr/en-US/pt-BR/ar 四种语言全部正确）
- [x] 真实验收发现并修复 3 个 Bug：① `UnicodeDecodeError`（`errors="replace"`）；② `--sub-langs` 重复追加；③ locale 字幕标签不匹配（`pt-BR` → 扩展为 `pt-BR-orig,pt-BR,pt-orig,pt`）
- [x] Bug 修复后复验通过：76 passed, 6 skipped；ruff 通过；doctor 通过
- [x] 推送后验证 CI 三平台绿灯（CI #28096484531）
- [x] 本轮文档状态同步后复验通过：79 passed, 3 skipped；ruff 通过；doctor 通过（Codex Python 3.12.13）
- [x] macOS playlist 下载校验：`yt-dlp` 可识别 11 条 playlist，但 YouTube 要求登录/反机器人确认，未下载媒体文件
- [x] 补强下载登录态支持：新增 `--cookies` / `--cookies-from-browser`，二者互斥；`--sub-langs original` 的语言探测会透传 cookie 来源并处理 playlist 多行语言输出
- [x] 登录态补强后标准验证通过：84 passed, 3 skipped；ruff 通过；doctor 通过（macOS ffmpeg / ffprobe / yt-dlp 均可用）
- [x] 使用 `--cookies-from-browser chrome` 复测 macOS playlist：前三条视频下载成功并经 ffprobe 验证为 H264 + AAC + MP4、1080p；第四条按用户要求中止，保留 `.part` 临时文件
- [x] macOS 兼容性补强：`verify.py` 提前检查 Python 3.11+ 并提示 Homebrew PEP 668 venv 路径；README 增加 macOS venv 验证命令；`fetch --dry-run --sub-langs original` 不再触发语言探测/浏览器 cookie 读取；批量下载 Ctrl-C 记录中断项以便写出 partial summary；macOS 默认配置/cache/data 目录改用 `~/Library/...`
- [x] macOS 补强后标准验证通过：86 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`
- [x] 自动友好命名：默认 `{lang}-{author}-{title}-{platform}.{ext}`；真实下载自动探测语言码；支持 `--name-template` 调整字段顺序、`--name-language` 手动覆盖、`--output-template` 原生覆盖；默认 `--windows-filenames` 处理作者/标题非法文件名字符
- [x] 自动命名补强后标准验证通过：106 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`
- [x] review 红灯修复：非法 fetch URL 在触发 yt-dlp 前校验；`--output-template` 禁止绝对路径与 `..`；CLI 默认 `--preset mp4` 与 core 对齐；并发重复 URL 不再覆盖结果；多语言字幕后缀不再折叠丢失
- [x] review 修复后标准验证通过：125 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`
- [x] review 黄灯收敛：CLI 错误输出接入 `core.logging`；fetch CLI 默认 3600 秒超时且支持 `--timeout 0` 不限时；命令分发改为映射；`ProcessRunner` 改为 Protocol 类型
- [x] review 黄灯收敛后标准验证通过：127 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`
- [x] review 完美绿灯收口：拆分 `core/fetch.py` 的认证/语言解析职责；拆分 `tests/test_fetch.py` 的参数构造与语言解析测试；所有 Python 文件降至 350 行预警线以下；CI 升级到 `actions/checkout@v7` / `actions/setup-python@v6` 并固定 macOS runner 为 `macos-15`
- [x] 完美绿灯收口后标准验证通过：127 passed, 6 skipped；ruff 通过；doctor 发现 `/opt/homebrew/bin/ffmpeg`、`ffprobe`、`yt-dlp`；最新推送 CI 三平台绿灯
- [x] review 追补硬化：字幕转换、fetch input-file、summary JSON 的文件 I/O 失败统一转为项目错误；字幕语言后缀后处理仅处理本次下载新增/变更字幕；并发下载 Ctrl-C 触发 executor 非等待关闭
- [x] review 追补硬化后标准验证通过：135 passed, 6 skipped；ruff 通过；doctor 发现 Windows `ffmpeg`、`ffprobe`、`yt-dlp`

## 6. 下一步建议

Phase 3 当前优先级：
1. **Legacy UI 兼容基线**：考古 Legacy 前端技术栈、布局、视觉规则和下载工作流，并补全 `docs/UI_COMPAT.md`。
2. **轻前端接口契约**：先冻结下载工作台所需的输入模型、输出模型、错误模型、任务进度模型和文件安全边界。
3. **轻前端 MVP**：优先做下载工作台，让项目能边开发边使用；前端只提交任务和展示状态，不复制媒体业务逻辑。
4. **后续功能评估**：下载与轻前端稳定后，再评估视频切片、资产扫描 / 搜索 / 统计。

## 7. 维护边界备忘

- **治理文档**：01-05 仅开发仓库使用，不随包分发。
- **`.agents/` 状态**：当前为空是正常状态；统一入口仍是根目录 `AGENTS.md`，除非需要多工具专属补充规则，否则不强制填充。
- **不提交**：构建产物、node_modules、__pycache__、.env、运行日志、数据库、vendor 残留。
- **跨平台优先**：所有路径处理使用 `mediatools.core.paths`。
- **依赖最小化**：慎重引入第三方依赖。
- **代码规模**：350 行预警，450 行评估拆分，500 行由 `scripts/verify.py` 硬性失败。
- **未验证不打钩**：客观项须先跑 `python scripts/verify.py`；主观项等待用户反馈；用户可见功能完成需两者都满足。
