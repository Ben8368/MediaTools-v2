# Current Context

## 1. 项目状态快照

> **更新时间：** 2026-06-24 15:11:05 +08:00
> **当前分支：** refactor-v2
> **当前阶段：** Phase 2 已完成，准备进入 Phase 3 - 功能增强与优化
> **验证状态：** 真实样本验收通过；`python scripts/verify.py` 通过（54 passed, 6 skipped；ruff 通过；doctor 通过）；CI 三平台绿灯

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

### 暂缓项
- Web UI / 桌面 GUI 推迟到核心 CLI 稳定、真实样本验收和接口契约清晰后评估。
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
- ✅ 前后端策略已澄清：不否定分离，延后到核心契约稳定后

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

## 6. 下一步建议

Phase 2 首批 MVP 已完成。下一步进入 Phase 3：
1. **下一批功能评估**：优先评估视频切片、资产扫描 / 搜索 / 统计。
2. **体验增强**：围绕真实样本暴露的需求补齐参数，例如 fetch 自动字幕已补 `--write-auto-subs`。
3. **架构边界**：暂不启动完整前后端架构，继续保持 core / CLI 适配层清晰。

## 7. 维护边界备忘

- **治理文档**：01-05 仅开发仓库使用，不随包分发。
- **不提交**：构建产物、node_modules、__pycache__、.env、运行日志、数据库、vendor 残留。
- **跨平台优先**：所有路径处理使用 `mediatools.core.paths`。
- **依赖最小化**：慎重引入第三方依赖。
- **代码规模**：350 行预警，450 行评估拆分，500 行默认禁止继续堆业务逻辑。
- **未验证不打钩**：客观项须先跑 `python scripts/verify.py`；主观项等待用户反馈；用户可见功能完成需两者都满足。
