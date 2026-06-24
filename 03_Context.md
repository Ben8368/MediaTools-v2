# Current Context

## 1. 项目状态快照

> **更新时间：** 2026-06-25 02:15:00 +08:00
> **当前分支：** refactor-v2
> **当前阶段：** Phase 3 - 真实批量下载验收通过
> **验证状态：** 真实 7 URL 批量下载验收通过（H264+AAC+MP4 + SRT 原语言字幕）；`python scripts/verify.py` 通过（76 passed, 6 skipped；ruff 通过；doctor 通过）；CI 待推送后复核

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

## 6. 下一步建议

Phase 3 当前优先级：
1. **下载工作流真实体验验收**：格式控制与原语言探测已就绪，可用真实批量任务验收完整流程（`--preset mp4 --convert-subs srt --sub-langs original`）。
2. **Legacy UI 兼容基线**：考古 Legacy 前端技术栈、布局、视觉规则和下载工作流，再启动 v2 轻前端工程。
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
