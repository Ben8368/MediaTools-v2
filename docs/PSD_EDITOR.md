# PSD 编辑器选型

> **状态：** `[待实现]`（Feature 024）。本文件只记录已确认的方案与边界；实施细节、代码草稿和历史方案见归档。

## 1. 方案结论

- **架构**：纯前端，浏览器内解析与编辑 PSD；后端零参与。
- **依赖**：`ag-psd`（解析/导出）+ `fabric`（Canvas 编辑），全部走前端 `npm`，运行时随浏览器加载，约 +400KB gzipped。
- **后端**：不引入 Node.js 运行时，不新增 Python 依赖；如需文件持久化，复用现有 `workspace` 端点，不另开 API。

## 2. 为什么是这个方案

- 符合 `01_Project_Plan.md` 的"小巧精悍、跨平台、依赖最小化"三条目标：后端依赖增量为 0，打包不引入第二套运行时。
- `ag-psd` 是同类库中文本层往返支持最完整、社区维护最活跃的实现；Python 侧 `psd-tools` 写入路径不可靠，已排除。

## 3. 边界

- 仅支持 RGB 8 位 PSD；CMYK、16/32 位色深暂不在 MVP 范围。
- 不在前端复制媒体业务逻辑：本特性仅做图像编辑，不与 `fetch`、`encode` 等核心命令耦合。

## 4. 归档

- 实施时的开发指南草稿：`docs/archive/2026-06-29_psd_editor_frontend_guide.md`
- 历史方案对比（混合架构、Python 轻量、Node.js 微服务，已全部放弃）：`docs/archive/psd-research/`
