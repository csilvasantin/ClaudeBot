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

function Write-LaunchStatus {
    param(
        [string]$Message,
        [string]$Color = "Gray"
    )
    $ts = Get-Date -Format 'HH:mm:ss'
    Write-Host "[$ts] " -NoNewline -ForegroundColor DarkGray
    Write-Host $Message -ForegroundColor $Color
}

Write-Host @"

   ____ _                 _      ____        _
  / ___| | __ _ _   _  __| | ___| __ )  ___ | |_
 | |   | |/ _`` | | | |/ _`` |/ _ \  _ \ / _ \| __|
 | |___| | (_| | |_| | (_| |  __/ |_) | (_) | |_
  \____|_|\__,_|\__,_|\__,_|\___|____/ \___/ \__|

"@ -ForegroundColor Cyan

Write-Host "  Auto-confirma solicitudes visuales de Claude Desktop" -ForegroundColor White
Write-Host "  Intervalo: ${Interval}s  |  Cooldown: ${Cooldown}s  |  Ventana: $WindowTitle" -ForegroundColor Gray
Write-Host "  ────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

if (-not (Test-Path .venv\Scripts\python.exe)) {
    Write-LaunchStatus "Creando entorno virtual..." "DarkCyan"
    python -m venv .venv
}

$pythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
Write-LaunchStatus "Revisando dependencias..." "DarkCyan"
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
    Write-LaunchStatus "ClaudeBot iniciado en segundo plano. PID: $($process.Id)" "Green"
    Write-LaunchStatus "Runtime log: $runtimeLog" "Gray"
    Write-LaunchStatus "Error log: $errorLog" "Gray"
    exit 0
}

Write-LaunchStatus "Entrando en modo vigilancia activa..." "Green"
& $pythonExe @args
