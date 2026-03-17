param(
    [string]$WindowTitle = "Claude",
    [string]$Template = "assets/claude_ctrl_enter_template.png",
    [double]$Threshold = 0.92,
    [double]$Interval = 5.0,
    [double]$Cooldown = 4.0,
    [string]$Region,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path .venv\Scripts\python.exe)) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements.txt | Out-Null
$env:PYTHONPATH = Join-Path $ProjectRoot 'src'

$args = @('-m', 'claudebot', 'run', '--window-title', $WindowTitle, '--template', $Template, '--threshold', "$Threshold", '--interval', "$Interval", '--cooldown', "$Cooldown")
if ($Region) {
    $args += @('--region', $Region)
}
if ($DryRun) {
    $args += '--dry-run'
}

& .\.venv\Scripts\python.exe @args
