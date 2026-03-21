# Launch ClaudeBot Watcher in its own window — kills previous watcher first
$script = Join-Path $PSScriptRoot "ClaudeBot-Watcher.ps1"
$pwsh = (Get-Process -Id $PID).Path
Get-Process pwsh -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*ClaudeBot-Watcher*" -and $_.Id -ne $PID } |
    Stop-Process -Force
Start-Process conhost.exe -ArgumentList "`"$pwsh`" -NoProfile -ExecutionPolicy Bypass -File `"$script`""
Write-Host "ClaudeBot watcher launched!" -ForegroundColor Green
