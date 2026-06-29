# PSD 编辑器技术调研归档

> 本目录保存 PSD 编辑器立项阶段的技术调研文档，**不代表当前实施方案**。
> 当前实施方案见上级目录 [`../PSD_EDITOR_README.md`](../PSD_EDITOR_README.md) 与 [`../PSD_EDITOR_FRONTEND.md`](../PSD_EDITOR_FRONTEND.md)。

## 文档清单

| 文件 | 内容 | 结论 |
|---|---|---|
| `psd-editing-reality-check.md` | 三种技术路径（纯 Python / Node.js / Photopea 前端）的深度对比 | ✅ **推导出最终方案的依据**：前端 ag-psd |
| `psd-editor-architecture.md` | 混合架构（后端自动化 + 前端可视化编辑） | ❌ 放弃，违背"小巧精悍" |
| `psd-editor-lightweight.md` | 纯 Python（psd-tools）+ 原生 Canvas 轻量方案 | ❌ 放弃，psd-tools 写入不可靠 |
| `mvp-plan.md` | Node.js 微服务 + Fabric.js 的 2 天 MVP 计划 | ❌ 放弃，引入 Node 运行时违背单一技术栈原则 |

## 历史

这 4 份文档原本位于 `backend-dev` 工作树的 `.planning/` 目录下。在调研结论确定为"纯前端方案"后，`backend-dev` 上的 PSD 实施计划报废，文档迁移至此集中保存，便于未来回溯决策过程。
