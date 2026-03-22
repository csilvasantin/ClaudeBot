# ============================================================
#  ClaudeBot Watcher — starts/stops ClaudeBot with Claude app
# ============================================================

param(
    [int]$Interval = 5
)

$botLauncher = Join-Path $PSScriptRoot "run_claudebot.ps1"
$pwsh = (Get-Process -Id $PID).Path

function Find-ClaudeWindow {
    $proc = Get-Process -Name "Claude" -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } |
        Select-Object -First 1
    if ($proc) { return $proc }
    Get-Process | Where-Object {
        $_.MainWindowTitle -like "*Claude*" -and $_.MainWindowHandle -ne [IntPtr]::Zero
    } | Select-Object -First 1
}

function Get-BotProcess {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -like '*python* -m claudebot run*' -or
            $_.CommandLine -like '*run_claudebot.ps1*'
        }
}

function Start-Bot {
    if (Get-BotProcess) { return }
    Start-Process conhost.exe -ArgumentList "`"$pwsh`" -NoProfile -ExecutionPolicy Bypass -File `"$botLauncher`" -ExitWhenWindowMissingAfter 2"
    Write-Host "[Watcher] Claude detected -> ClaudeBot launched" -ForegroundColor Green
}

function Stop-Bot {
    $procs = Get-BotProcess
    if (-not $procs) { return }
    $procs | ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {}
    }
    Write-Host "[Watcher] Claude closed -> ClaudeBot stopped" -ForegroundColor Yellow
}

Write-Host "ClaudeBot Watcher running. Press q to stop." -ForegroundColor Cyan

while ($true) {
    try {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if ($key.KeyChar -eq 'q' -or $key.KeyChar -eq 'Q') {
                Stop-Bot
                break
            }
        }
    } catch {}

    if (Find-ClaudeWindow) {
        Start-Bot
    } else {
        Stop-Bot
    }

    Start-Sleep -Seconds $Interval
}

Write-Host "ClaudeBot Watcher finished." -ForegroundColor Cyan
