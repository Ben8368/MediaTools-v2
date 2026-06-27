# prepare-commit-msg.ps1
# Automatically adds a Co-Authored-By trailer for the AI development tool
# driving the commit, based on environment variables each tool injects.
#
# NOTE: Git for Windows runs hooks through Git Bash, so the bash
# `prepare-commit-msg` script is what actually executes on commit. This
# PowerShell version is kept in sync for environments that invoke it directly.
#
# Manual override (highest priority):
#   git config mediatools.ai-tool <claude|codex|cursor|opencode>

param(
    [string]$CommitMsgFile,
    [string]$CommitSource
)

# --- Canonical co-author identities (GitHub-username convention) -----------
$CLAUDE_COAUTHOR   = "Co-Authored-By: claude <claude@noreply.anthropic.com>"
$CODEX_COAUTHOR    = "Co-Authored-By: codex <codex@openai.com>"
$CURSOR_COAUTHOR   = "Co-authored-by: cursoragent <cursoragent@cursor.com>"
$OPENCODE_COAUTHOR = "Co-Authored-By: opencode <opencode@noreply.local>"

# Skip if the message already carries a Co-Authored-By trailer.
$content = Get-Content $CommitMsgFile -Raw -ErrorAction SilentlyContinue
if ($content -match "(?i)Co-Authored-By:") {
    exit 0
}

# Skip for merge/squash commits.
if ($CommitSource -eq "merge" -or $CommitSource -eq "squash") {
    exit 0
}

function Detect-AITool {
    # 1. Explicit manual override via git config.
    $hint = (git config --get mediatools.ai-tool 2>$null)
    switch ($hint) {
        { $_ -in @("claude", "claude-code") } { return $CLAUDE_COAUTHOR }
        "codex"    { return $CODEX_COAUTHOR }
        "cursor"   { return $CURSOR_COAUTHOR }
        "opencode" { return $OPENCODE_COAUTHOR }
    }

    # 2. Claude Code.
    if ($env:CLAUDECODE -or $env:CLAUDE_CODE -or $env:CLAUDE_CODE_SESSION_ID `
        -or $env:CLAUDE_CODE_ENTRYPOINT -or ($env:AI_AGENT -like "claude-code*")) {
        return $CLAUDE_COAUTHOR
    }

    # 3. OpenAI Codex CLI.
    if ($env:CODEX_SANDBOX -or $env:CODEX_CI -or $env:CODEX_THREAD_ID) {
        return $CODEX_COAUTHOR
    }

    # 4. Cursor agent.
    if ($env:CURSOR_AGENT -or ($env:CURSOR_EXTENSION_HOST_ROLE -eq "agent-exec")) {
        return $CURSOR_COAUTHOR
    }

    # 5. opencode.
    if ($env:OPENCODE_CLIENT -or $env:OPENCODE_SESSION -or $env:OPENCODE_COAUTHOR) {
        return $OPENCODE_COAUTHOR
    }

    return $null
}

$aiCoauthor = Detect-AITool

if ($aiCoauthor -and (Test-Path $CommitMsgFile)) {
    $content = Get-Content $CommitMsgFile -Raw
    if ($content -and -not $content.EndsWith("`n")) {
        $content += "`n"
    }
    $content += "`n$aiCoauthor`n"
    Set-Content -Path $CommitMsgFile -Value $content -NoNewline
}

exit 0
