---

## ⚙️ 工作流协议

### 每次对话开始时
1. **读取治理文档**：`AGENTS.md` → `01`-`05`
2. **确认项目状态**：检查 `03_Context.md`
3. **扫描历史教训**：读取 `05_Lessons.md`
4. **若标记 [未初始化]**：执行技术栈访谈

### 代码生成时
1. **思考**：查阅 `05` 相关教训
2. **编码**：遵循 `02` 规范
3. **审查**：执行红绿灯评估 🚦
4. **验证**：AI 自行执行 `python scripts/verify.py`，附结果摘要
5. **提交**：若 Audit Report 为 🟢 完美且客观验证通过，AI 自动本地提交并推送远端；提交需添加对应 AI 工具的 Co-Authored-By 标记（见下文"Git Commit 规范"）
6. **推进**：客观项全绿则更新治理文档并继续；主观项再询问用户

### 验证分层

| 类型 | 执行者 | 示例 |
| --- | --- | --- |
| **客观验证** | AI + `scripts/verify.py` + CI | pytest、ruff、安装、doctor、ffmpeg/PATH 报告 |
| **主观验收** | 用户 | 功能好不好用、输出是否合理、MVP 范围 |

原则：**不要求用户重复执行 AI 已能跑的命令**。用户反馈应聚焦体验与业务判断。

### 客观验证通过后
1. 获取准确时间
2. 更新 `03_Context.md` 与 `04_Features.md`
3. 固化经验到 `05_Lessons.md`（如有）
4. 若最终 Audit Report 为 🟢 完美，则自动提交并推送当前分支；若为 🟡/🔴，不得自动提交
5. 推进下一步任务

推送后以 CI 绿灯作为跨平台验收依据。

---

## 🎯 关键原则

### 跨平台优先
- ✅ 使用标准库路径处理
- ✅ 环境变量获取标准 API
- ✅ 文件编码显式 UTF-8
- ❌ 禁止硬编码路径分隔符
- ❌ 禁止平台特定系统调用

### 依赖最小化
- 优先标准库
- 慎重引入第三方包
- 评估：必需性、维护状态、许可证

### 验证与打钩
- 客观项：AI 跑 `verify.py` + CI 绿 → 可标 `[已完成]`
- 主观项：标 `[待完善]` 或等待用户反馈
- 严禁未跑验证就打钩

### Git Commit 规范

所有 AI 辅助开发的提交**必须**添加 `Co-Authored-By` 标记，用于追踪各工具贡献：

| AI 工具 | Co-Authored-By 标记 |
|---------|---------------------|
| Claude Code | `Co-Authored-By: claude <claude@noreply.anthropic.com>` |
| Cursor | `Co-authored-by: cursoragent <cursoragent@cursor.com>` |
| Codex | `Co-Authored-By: codex <codex@openai.com>` |
| OpenCode | `Co-Authored-By: opencode <opencode@noreply.local>` |
| OpenClaw | `Co-Authored-By: openclaw <openclaw@noreply.local>` |

**自动化方式**：
- 安装 Git hook：`.git-hooks/install.ps1`（Windows）或 `cp .git-hooks/prepare-commit-msg .git/hooks/`（Linux/macOS）
- Hook 会自动检测当前 AI 工具并添加对应标记

**详细配置**：见 `docs/AI_COAUTHOR_SETUP.md`

---

## 🔗 关联资源

- **Legacy 版本**：https://github.com/Ben8368/MediaTools （仅作参考）
- **新仓库**：https://github.com/Ben8368/MediaTools-v2
- **治理体系来源**：weibo-workflow 项目经验
