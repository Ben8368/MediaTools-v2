# AI 开发工具自动添加 Co-Author 指南

本项目支持多种方式让 AI 开发工具自动在 commit 中添加 co-author 标记，方便统计各工具的贡献。

## 快速开始

### 方法 1：使用 Git Hook（推荐，自动化）

```powershell
# 安装 hook
.\.git-hooks\install.ps1

# 测试
git commit -m "test: verify co-author hook"
git log -1 --pretty=format:'%B'
```

Hook 会自动检测当前使用的 AI 工具并添加对应的 co-author。

### 方法 2：使用 Commit Template（手动提示）

项目已配置 `.gitmessage` 模板，执行 `git commit` 时会显示模板提示你添加 co-author。

### 方法 3：手动添加（备用）

```bash
git commit -m "feat: add new feature

Co-Authored-By: Codex <codex@openai.com>"
```

或修改最近的提交：

```bash
git commit --amend
# 在编辑器中添加 co-author 行
```

## 支持的 AI 工具及标记

| 工具 | Co-Author 标记 | 检测方式 |
|------|---------------|---------|
| **Claude Code** | `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` | 环境变量 `CLAUDE_CODE_SESSION` 或进程名 |
| **Claude Sonnet** | `Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>` | 手动指定 |
| **Claude Haiku** | `Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>` | 手动指定 |
| **Cursor** | `Co-authored-by: Cursor <cursoragent@cursor.com>` | 环境变量 `CURSOR_SESSION_ID` 或进程名 |
| **GitHub Copilot/Codex** | `Co-Authored-By: Codex <codex@openai.com>` | VS Code + Copilot 进程检测 |
| **OpenCode** | `Co-Authored-By: OpenCode <opencode@byted.org>` | 环境变量 `OPENCODE_SESSION` |
| **WorkBuddy** | `Co-Authored-By: WorkBuddy <workbuddy@example.com>` | 环境变量 `WORKBUDDY_SESSION` |

## 各工具详细配置

### Claude Code CLI

✅ **自动支持** - Claude Code 会自动添加 co-author，无需额外配置。

如果未自动添加，确保使用最新版本。

### Cursor

✅ **自动支持** - Cursor 内置 co-author 功能。

如果未生效：
1. Settings → Features → Git
2. 启用 "Add Cursor as co-author"

### GitHub Copilot / Codex

⚠️ **需要 Hook** - Copilot 本身不自动添加 co-author。

使用方法：
1. 安装本项目的 Git hook（见上方"快速开始"）
2. Hook 会检测 VS Code + Copilot 进程并自动添加

或手动添加：
```bash
git commit -m "feat: your message" -m "" -m "Co-Authored-By: Codex <codex@openai.com>"
```

### OpenCode（字节内部）

⚠️ **需要环境变量**

```bash
# 在你的 shell 配置中添加
export OPENCODE_SESSION=1
export OPENCODE_COAUTHOR="OpenCode <opencode@byted.org>"
```

### WorkBuddy

⚠️ **需要环境变量**

```bash
export WORKBUDDY_SESSION=1
```

## Hook 工作原理

Hook 位于 `.git/hooks/prepare-commit-msg`，在你执行 `git commit` 时自动运行。

检测逻辑：
1. 检查环境变量（`CLAUDE_CODE_SESSION`, `CURSOR_SESSION_ID` 等）
2. 检查当前运行的进程（`claude-code`, `Cursor`, `Code` 等）
3. 如果检测到 AI 工具，自动在 commit message 末尾追加对应的 co-author

跳过条件：
- Commit message 中已有 `Co-Authored-By:`
- Merge commit 或 squash commit

## 验证和调试

### 检查最近的 commit 是否有 co-author

```bash
git log -1 --pretty=format:'%h|%an|%(trailers:key=Co-authored-by,valueonly)|%s'
```

### 查看所有 contributors

```bash
git log --pretty=format:'%an|%(trailers:key=Co-authored-by,valueonly)' | sort | uniq -c
```

### 手动触发 hook 测试

```bash
# 创建测试文件
echo "test commit message" > .git/COMMIT_EDITMSG

# 运行 hook
.git/hooks/prepare-commit-msg .git/COMMIT_EDITMSG

# 查看结果
cat .git/COMMIT_EDITMSG
```

### Hook 不生效？

1. **检查 hook 是否安装**：
   ```bash
   ls -la .git/hooks/prepare-commit-msg
   ```

2. **检查 hook 是否可执行**：
   ```bash
   chmod +x .git/hooks/prepare-commit-msg
   ```

3. **手动运行查看错误**：
   ```powershell
   .\.git-hooks\prepare-commit-msg.ps1 ".git\COMMIT_EDITMSG" ""
   ```

4. **禁用其他冲突的 Git 工具**：
   某些 GUI 工具（如 SourceTree）可能覆盖 hooks。

## GitHub Contributors 统计

添加 co-author 后，可以在 GitHub 的 contributors 页面看到统计：

- https://github.com/Ben8368/MediaTools-v2/graphs/contributors

注意：
- 需要等待几分钟让 GitHub 重新计算
- 邮箱对应的 GitHub 账号才会显示头像
- 无账号的邮箱会显示为邮箱地址

## 批量修复历史提交

如果之前的提交缺少 co-author，可以批量修复：

```bash
# 查看需要修复的提交
git log --pretty=format:'%h|%s' --all | grep -v "Co-Authored-By"

# 使用 filter-branch 批量添加（慎用，会改写历史）
# 见 docs/AI_COMMIT_GUIDE.md 的详细步骤
```

⚠️ **警告**：改写历史需要强制推送，会影响所有协作者。

## 文件结构

```
.git-hooks/                    # Hook 脚本目录
├── prepare-commit-msg         # Bash 版本 hook
├── prepare-commit-msg.ps1     # PowerShell 版本 hook
└── install.ps1                # 安装脚本

.git/hooks/
└── prepare-commit-msg         # 实际生效的 hook（包装脚本）

.gitmessage                    # Commit message 模板
docs/AI_COMMIT_GUIDE.md        # 详细文档
```

## 卸载

如果需要移除自动 co-author 功能：

```bash
rm .git/hooks/prepare-commit-msg
git config --unset commit.template
```

## 贡献

如果你使用的 AI 工具不在支持列表中，欢迎提交 PR 添加检测逻辑。

需要提供：
1. 工具名称
2. 标准的 co-author 邮箱格式
3. 检测方式（环境变量、进程名等）
