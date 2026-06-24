# MediaTools v2 - Refactor Plan

> **提示**：本项目采用治理文档体系，AI 工具请先阅读 `AGENTS.md`

## 🎯 重构目标

### 核心问题
Legacy 版本（https://github.com/Ben8368/MediaTools）存在以下问题：
- ❌ 包含大量 vendor 依赖（yt-dlp, capcut-mate 等）
- ❌ 大文件问题（58MB+ 配置文件无法推送）
- ❌ 密钥检测触发（vendor 代码中的示例密钥）
- ❌ 架构过度复杂（前后端分离、过度抽象）

### 重构原则
1. **小巧精悍**：最小依赖，核心功能优先
2. **跨平台优先**：Windows / macOS / Linux 统一体验
3. **模块化**：功能独立，按需加载
4. **可测试**：核心逻辑与 I/O 分离

---

## 📁 治理体系

本项目采用 **01-05 治理文档** + **AGENTS.md** 入口：

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | AI 工具统一入口 |
| `01_Project_Plan.md` | 项目蓝图与技术栈 |
| `02_AI_Rules.md` | AI 行为准则与审查系统 |
| `03_Context.md` | 实时状态快照 |
| `04_Features.md` | 功能评估池与 ADR |
| `05_Lessons.md` | 经验教训与避坑指南 |

**AI 工具使用流程**：读取 `AGENTS.md` → 按序读取 `01`-`05` → 开始工作

---

## 🚀 Roadmap

详见 `01_Project_Plan.md` §2，当前阶段：

- [x] Phase 0：治理初始化
  - [x] 创建极简结构
  - [x] 建立治理文档体系
  - [x] 技术栈决策（Python CLI 优先）
  - [ ] 明确首批核心功能清单（暂缓，待完善）
- [ ] Phase 1：核心架构搭建（进行中）
  - [ ] 跨平台路径处理模块（待验证）
  - [ ] 基础 CI（待验证）
- [ ] Phase 2：从 Legacy 迁移功能
- [ ] Phase 3：功能增强与优化

---

## 🔄 从 Legacy 迁移

### 保留价值
- 核心媒体处理逻辑
- 已验证的工作流
- 跨平台路径处理经验

### 舍弃部分
- 所有 vendor 目录 → 使用系统工具或轻量库
- 前后端分离架构 → 单体 CLI 优先
- 过度抽象层次 → 简化实现

### 迁移策略
详见 `04_Features.md` Feature-002
