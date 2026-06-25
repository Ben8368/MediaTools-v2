# Install Git Hooks for AI Co-Author Tracking
# Run this script to set up automatic co-author detection

Write-Host "Installing Git hooks for AI co-author tracking..." -ForegroundColor Cyan

$repoRoot = git rev-parse --show-toplevel
if (-not $repoRoot) {
    Write-Host "Error: Not in a git repository" -ForegroundColor Red
    exit 1
}

# Create hooks directory if it doesn't exist
$hooksDir = Join-Path $repoRoot ".git\hooks"
if (-not (Test-Path $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
}

# Copy wrapper script
$wrapperSource = Join-Path $repoRoot ".git-hooks\prepare-commit-msg"
$wrapperDest = Join-Path $hooksDir "prepare-commit-msg"

if (Test-Path $wrapperSource) {
    Copy-Item -Path $wrapperSource -Destination $wrapperDest -Force
    Write-Host "✅ Installed prepare-commit-msg hook wrapper" -ForegroundColor Green
} else {
    Write-Host "❌ Hook wrapper not found at $wrapperSource" -ForegroundColor Red
}

# Make hook executable (Git Bash compatibility)
git update-index --chmod=+x .git/hooks/prepare-commit-msg 2>$null

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "The hook will now automatically detect and add co-authors for:" -ForegroundColor Yellow
Write-Host "  - Claude Code  (CLAUDECODE / CLAUDE_CODE_* / AI_AGENT)" -ForegroundColor White
Write-Host "  - OpenAI Codex (CODEX_SANDBOX / CODEX_CI / CODEX_THREAD_ID)" -ForegroundColor White
Write-Host "  - Cursor agent (CURSOR_AGENT / CURSOR_EXTENSION_HOST_ROLE)" -ForegroundColor White
Write-Host "  - opencode     (OPENCODE_CLIENT / OPENCODE_SESSION)" -ForegroundColor White
Write-Host ""
Write-Host "Manual override (if auto-detection misses your tool):" -ForegroundColor Yellow
Write-Host "  git config mediatools.ai-tool <claude|codex|cursor|opencode>" -ForegroundColor White
Write-Host ""
Write-Host "Test it with: git commit -m 'test: verify co-author hook'" -ForegroundColor Cyan
Write-Host "Then check with: git log -1 --pretty=format:'%B'" -ForegroundColor Cyan
