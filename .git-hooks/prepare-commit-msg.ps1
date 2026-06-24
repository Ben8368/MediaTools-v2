# prepare-commit-msg.ps1
# Automatically adds Co-Authored-By trailer for AI development tools
#
# Install: Copy to .git\hooks\prepare-commit-msg (no extension) and make it call this script

param(
    [string]$CommitMsgFile,
    [string]$CommitSource
)

# Skip if commit message already has Co-Authored-By
$content = Get-Content $CommitMsgFile -Raw -ErrorAction SilentlyContinue
if ($content -match "(?i)Co-Authored-By:") {
    exit 0
}

# Skip for merge/squash commits
if ($CommitSource -eq "merge" -or $CommitSource -eq "squash") {
    exit 0
}

# Detect which AI tool is running
function Detect-AITool {
    # Check environment variables

    # Claude Code CLI
    if ($env:CLAUDE_CODE_SESSION -or (Get-Process -Name "claude-code" -ErrorAction SilentlyContinue)) {
        return "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
    }

    # Cursor
    if ($env:CURSOR_SESSION_ID -or (Get-Process -Name "Cursor" -ErrorAction SilentlyContinue)) {
        return "Co-authored-by: Cursor <cursoragent@cursor.com>"
    }

    # GitHub Copilot / Codex (check for VS Code with Copilot)
    if ((Get-Process -Name "Code" -ErrorAction SilentlyContinue) -and $env:VSCODE_GIT_ASKPASS_NODE) {
        # Assume Codex if VS Code is running with git integration
        return "Co-Authored-By: Codex <codex@openai.com>"
    }

    # OpenCode (字节内部)
    if ($env:OPENCODE_SESSION -or $env:OPENCODE_COAUTHOR) {
        return "Co-Authored-By: OpenCode <opencode@byted.org>"
    }

    # WorkBuddy
    if ($env:WORKBUDDY_SESSION) {
        return "Co-Authored-By: WorkBuddy <workbuddy@example.com>"
    }

    # Check TERM_PROGRAM
    if ($env:TERM_PROGRAM -eq "Cursor") {
        return "Co-authored-by: Cursor <cursoragent@cursor.com>"
    }

    # Check parent process names
    $parentProcess = (Get-WmiObject Win32_Process -Filter "ProcessId=$PID").ParentProcessId
    if ($parentProcess) {
        $parent = Get-Process -Id $parentProcess -ErrorAction SilentlyContinue
        if ($parent) {
            switch ($parent.ProcessName) {
                "Cursor" { return "Co-authored-by: Cursor <cursoragent@cursor.com>" }
                "Code" { return "Co-Authored-By: Codex <codex@openai.com>" }
            }
        }
    }

    return $null
}

# Detect AI tool
$aiCoauthor = Detect-AITool

# If AI tool detected, append co-author
if ($aiCoauthor) {
    if (Test-Path $CommitMsgFile) {
        # Ensure file ends with newline
        $content = Get-Content $CommitMsgFile -Raw
        if ($content -and -not $content.EndsWith("`n")) {
            $content += "`n"
        }
        $content += "`n$aiCoauthor`n"
        Set-Content -Path $CommitMsgFile -Value $content -NoNewline
    }
}

exit 0
