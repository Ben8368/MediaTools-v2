---

## 工作流协议

### 每次对话开始时
1. **读入口**：`AGENTS.md`、`03_Context.md`、`05_Lessons.md`。
2. **确认状态**：以 `03_Context.md` 的当前快照、阻断项和下一步为准。
3. **匹配错题**：按任务关键词查 `05_Lessons.md` 的主题规则；只在需要背景时读取归档全文。
4. **按需扩展**：
   - 架构/编码规则：读 `02_AI_Rules.md`
   - 阶段计划：读 `01_Project_Plan.md`
   - 功能/ADR 详情：读 `04_Features.md`，必要时再读 `docs/archive/`
5. **若标记 `[未初始化]`**：执行技术栈访谈。

### 代码生成时
1. **思考**：查 `05_Lessons.md` 中与当前任务相关的规则。
2. **编码**：遵循 `02_AI_Rules.md` 与现有代码风格。
3. **审查**：执行红绿灯评估。
4. **验证**：AI 自行执行 `python scripts/verify.py`，附结果摘要。
5. **提交**：若 Audit Report 为 `🟢 完美` 且客观验证通过，AI 自动本地提交并推送远端；提交需添加对应 AI 工具的 `Co-Authored-By` 标记。
6. **推进**：客观项全绿则更新治理文档；主观项等待用户反馈。

### 验证分层

| 类型 | 执行者 | 示例 |
| --- | --- | --- |
| 客观验证 | AI + `scripts/verify.py` + CI | pytest、ruff、安装、doctor、ffmpeg/PATH 报告 |
| 主观验收 | 用户 | 功能好不好用、输出是否合理、MVP 范围 |

原则：不要求用户重复执行 AI 已能跑的命令。用户反馈聚焦体验与业务判断。

### 客观验证通过后
1. 获取准确时间。
2. 更新 `03_Context.md` 与 `04_Features.md` 的当前状态。
3. 仅在出现可复用新经验时更新 `05_Lessons.md`；详细过程归档到 `docs/archive/`。
4. 若最终 Audit Report 为 `🟢 完美`，自动提交并推送当前分支；若为 `🟡/🔴`，不得自动提交。
5. 推送后以 CI 绿灯作为跨平台验收依据。

---

## 关键原则

### 跨平台优先
- 使用标准库路径处理。
- 环境变量获取使用标准 API。
- 文件编码显式 UTF-8。
- 禁止硬编码路径分隔符。
- 禁止平台特定系统调用。

### 依赖最小化
- 优先标准库。
- 慎重引入第三方包。
- 引入前评估必需性、维护状态和许可证。

### 验证与打钩
- 客观项：AI 跑 `verify.py` + CI 绿后可标 `[已完成]` 或 `[客观已验证]`。
- 主观项：标 `[待完善]` 或等待用户反馈。
- 严禁未跑验证就打钩。

### Git Commit 规范

所有 AI 辅助开发提交必须添加 `Co-Authored-By` 标记：

| AI 工具 | Co-Authored-By 标记 |
| --- | --- |
| Claude Code | `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` |
| Cursor | `Co-authored-by: cursoragent <cursoragent@cursor.com>` |
| Codex | `Co-Authored-By: codex <codex@openai.com>` |
| OpenCode | `Co-Authored-By: opencode <opencode@noreply.local>` |
| OpenClaw | `Co-Authored-By: openclaw <openclaw@noreply.local>` |

**语言要求**：所有 commit message（包括 subject 和 body）必须使用英文，以保持代码仓库国际化标准。

自动化方式：
- Windows：`.git-hooks/install.ps1`
- Linux/macOS：`cp .git-hooks/prepare-commit-msg .git/hooks/`
- 详细配置：`docs/AI_COAUTHOR_SETUP.md`

---

## 关联资源

- Legacy 版本：https://github.com/Ben8368/MediaTools
- 新仓库：https://github.com/Ben8368/MediaTools-v2
- 完整治理归档：`docs/archive/`
