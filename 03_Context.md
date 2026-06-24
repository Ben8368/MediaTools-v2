# Current Context

## 1. 项目状态快照

> **更新时间：** 2026-06-24 12:57:11 +08:00
> **当前分支：** refactor-v2
> **当前阶段：** Phase 1 - 核心架构搭建
> **验证状态：** 路径模块与 CI 已通过本地与远端验证

## 2. 本轮阻断项

- [x] 同步治理文档状态（REFACTOR、04、01）
- [x] 补强 `02_AI_Rules.md`
- [x] 实现 `core/paths` 跨平台路径模块
- [x] 添加 GitHub Actions CI 工作流
- [x] 用户验证路径模块与 CI（本地 9 passed + ruff；CI #28076101163 三平台绿灯）

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
- Web UI / 桌面 GUI 推迟到核心 CLI 稳定后评估。
- 单文件可执行程序分发推迟到发布准备阶段评估。
- **核心功能清单 / MVP 范围**：暂缓，保留 `[待完善]` 状态。

## 4. 知识库关联

> **Legacy 版本：** https://github.com/Ben8368/MediaTools  
> **新仓库：** https://github.com/Ben8368/MediaTools-v2  
> **当前分支：** refactor-v2

### 关键决策
- ✅ 采用治理文件体系（参考 weibo-workflow）
- ✅ 全新 orphan 分支重构，不保留历史包袱
- ✅ 技术栈采用 Python CLI 优先
- ⏳ 核心功能清单待完善（暂缓）
- ✅ 工程脚手架已通过验证
- ✅ `core/paths` 与 CI 已通过验证

## 5. 当前任务焦点

- [x] 建立治理文档入口（01-05 + AGENTS.md）
- [x] 完成技术栈决策访谈
- [x] 验证 Python CLI 最小脚手架
- [x] 同步文档状态、补强 AI 规则
- [x] 实现跨平台路径模块（`src/mediatools/core/paths.py`）
- [x] 添加 CI 工作流（`.github/workflows/ci.yml`）
- [x] 用户验证路径模块与 CI
- [ ] 从 Legacy 版本提取核心功能清单（暂缓）

## 6. 下一步建议

- 日志系统
- 错误处理体系
- 配置加载与工作区目录约定

## 7. 维护边界备忘

- **治理文档**：01-05 仅开发仓库使用，不随包分发。
- **不提交**：构建产物、node_modules、__pycache__、.env、运行日志、数据库、vendor 残留。
- **跨平台优先**：所有路径处理使用 `mediatools.core.paths`。
- **依赖最小化**：慎重引入第三方依赖。
- **未验证不打钩**：客观项须先跑 `python scripts/verify.py`；主观项等待用户反馈。
