# AI 开发工具 Commit 规范

本项目使用 Git co-author 机制追踪 AI 工具贡献。所有 AI 辅助开发的提交都应添加相应的 `Co-Authored-By` 标记。

## Commit Message 格式

```
<type>(<scope>): <subject>

<body (optional)>

Co-Authored-By: <AI Tool Name> <email>
```

### 语言规范

**所有 commit message 必须使用英文**，包括 subject 和 body 部分。

- ✅ 正确：`feat(psd): add PSD editor with ag-psd integration`
- ❌ 错误：`feat(psd): 添加 PSD 编辑器`

原因：
- 保持代码仓库国际化标准
- 确保 GitHub/GitLab 等平台正确显示和索引
- 便于开源协作和团队协作

## AI 工具 Co-Author 列表

当前标准以根目录 `AGENTS.md` 为准：

| 工具 | Co-Authored-By 标记 |
|------|---------------------|
| Claude Code | `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` |
| Cursor | `Co-authored-by: cursoragent <cursoragent@cursor.com>` |
| Codex | `Co-Authored-By: codex <codex@openai.com>` |
| OpenCode | `Co-Authored-By: opencode <opencode@noreply.local>` |
| OpenClaw | `Co-Authored-By: openclaw <openclaw@noreply.local>` |

## 自动化配置

### 1. Git Commit Template

项目已配置 `.gitmessage` 模板，会在 commit 时自动加载提示。

### 2. Git Hooks（推荐）

使用 `prepare-commit-msg` hook 自动识别当前 AI 工具并添加 co-author：

```bash
# 安装
cp .git-hooks/prepare-commit-msg .git/hooks/
chmod +x .git/hooks/prepare-commit-msg
```

### 3. 手动添加

如果自动化失败，可以手动在 commit message 末尾追加：

```bash
git commit -m "feat: add new feature

Co-Authored-By: codex <codex@openai.com>"
```

或使用 `git commit --amend` 修改最近的提交。

## 各工具配置指南

### Claude Code CLI

Claude Code 自动添加 co-author，无需额外配置。

### Cursor

Cursor 会自动添加或应手动补齐 `Co-authored-by: cursoragent <cursoragent@cursor.com>`。

如果未自动添加，在 Cursor 设置中启用：
- Settings → Features → Git → "Add Cursor as co-author"

### Codex / GitHub Copilot

需要通过 commit template 或 hook 自动添加。

### OpenCode

OpenCode 需要配置环境变量或手动补齐标准 trailer：
```bash
export OPENCODE_COAUTHOR="Co-Authored-By: opencode <opencode@noreply.local>"
```

### OpenClaw

若自动化未覆盖，手动补齐 `Co-Authored-By: openclaw <openclaw@noreply.local>`。

## 验证

提交后检查 co-author 是否正确：

```bash
git log -1 --pretty=format:'%h|%an|%(trailers:key=Co-authored-by,valueonly)|%s'
```

## GitHub Contributors 统计

添加 co-author 后，GitHub 会将对应的工具显示在：
- https://github.com/Ben8368/MediaTools-v2/graphs/contributors

注意：
- 邮箱需要对应 GitHub 账号才会显示头像
- 统计更新可能需要几分钟
