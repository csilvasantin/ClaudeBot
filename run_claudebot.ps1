param(
    [string]$WindowTitle = "Claude",
    [string]$Template = "assets/claude_ctrl_enter_template.png",
    [double]$Threshold = 0.92,
    [double]$Interval = 5.0,
    [double]$Cooldown = 4.0,
    [double]$MouseIdleSeconds = 5.0,
    [string]$EvidenceDir = "evidence",
    [string]$Region,
    [switch]$DryRun,
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path .venv\Scripts\python.exe)) {
    python -m venv .venv
}

$pythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
& $pythonExe -m pip install -r requirements.txt | Out-Null
& $pythonExe -m pip install -e . | Out-Null

$args = @(
    '-m', 'claudebot', 'run',
    '--window-title', $WindowTitle,
    '--template', $Template,
    '--threshold', "$Threshold",
    '--interval', "$Interval",
    '--cooldown', "$Cooldown",
    '--mouse-idle-seconds', "$MouseIdleSeconds",
    '--evidence-dir', $EvidenceDir
)
if ($Region) {
    $args += @('--region', $Region)
}
if ($DryRun) {
    $args += '--dry-run'
}

if ($Background) {
    Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -like '*python.exe* -m claudebot run*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

    $runtimeLog = Join-Path $ProjectRoot 'claudebot.runtime.log'
    $errorLog = Join-Path $ProjectRoot 'claudebot.error.log'

    $process = Start-Process -FilePath $pythonExe -ArgumentList $args -WorkingDirectory $ProjectRoot -RedirectStandardOutput $runtimeLog -RedirectStandardError $errorLog -PassThru
    Write-Host "ClaudeBot iniciado en segundo plano. PID: $($process.Id)"
    Write-Host "Runtime log: $runtimeLog"
    Write-Host "Error log: $errorLog"
    exit 0
}

& $pythonExe @args
