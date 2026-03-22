param(
    [string]$WindowTitle = "Claude",
    [string]$Template = "assets/claude_ctrl_enter_template.png",
    [double]$Threshold = 0.92,
    [double]$Interval = 5.0,
    [double]$Cooldown = 4.0,
    [double]$MouseIdleSeconds = 5.0,
    [string]$EvidenceDir = "evidence",
    [string]$Region,
    [int]$ExitWhenWindowMissingAfter = 0,
    [switch]$DryRun,
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$esc = [char]27
$ClaudePrimary = "${esc}[38;2;217;119;87m"
$ClaudeSecondary = "${esc}[38;2;245;232;215m"
$ClaudeMuted = "${esc}[38;2;143;148;156m"
$ClaudeDivider = "${esc}[38;2;120;72;52m"
$ResetColor = "${esc}[0m"

function Write-LaunchStatus {
    param(
        [string]$Message,
        [string]$Color = "Gray"
    )
    $ts = Get-Date -Format 'HH:mm:ss'
    Write-Host "${ClaudeMuted}[$ts]${ResetColor} " -NoNewline
    switch ($Color) {
        "ClaudePrimary" { Write-Host "${ClaudePrimary}$Message${ResetColor}" }
        "ClaudeSecondary" { Write-Host "${ClaudeSecondary}$Message${ResetColor}" }
        "ClaudeMuted" { Write-Host "${ClaudeMuted}$Message${ResetColor}" }
        default { Write-Host $Message -ForegroundColor $Color }
    }
}

Write-Host @"

   ______ _                 _      ____        _
  / ____/| | __ _ _   _  __| | ___| __ )  ___ | |_
 / /    | |/ _`` | | | |/ _`` |/ _ \  _ \ / _ \| __|
/ /___  | | (_| | |_| | (_| |  __/ |_) | (_) | |_
\____/  |_|\__,_|\__,_|\__,_|\___|____/ \___/ \__|

"@ -ForegroundColor DarkYellow

Write-Host "  ${ClaudeSecondary}Auto-confirma solicitudes visuales de Claude Desktop${ResetColor}"
Write-Host "  ${ClaudeMuted}Intervalo: ${Interval}s  |  Cooldown: ${Cooldown}s  |  Ventana: $WindowTitle${ResetColor}"
Write-Host "  ${ClaudeMuted}Salida al faltar Claude: $(if ($ExitWhenWindowMissingAfter -gt 0) { $ExitWhenWindowMissingAfter } else { 'desactivada' })${ResetColor}"
Write-Host "  ${ClaudeDivider}────────────────────────────────────────${ResetColor}"
Write-Host ""

if (-not (Test-Path .venv\Scripts\python.exe)) {
    Write-LaunchStatus "Creando entorno virtual..." "ClaudeMuted"
    python -m venv .venv
}

$pythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
Write-LaunchStatus "Revisando dependencias..." "ClaudeMuted"
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
    '--evidence-dir', $EvidenceDir,
    '--exit-when-window-missing-after', "$ExitWhenWindowMissingAfter"
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
    Write-LaunchStatus "ClaudeBot iniciado en segundo plano. PID: $($process.Id)" "ClaudePrimary"
    Write-LaunchStatus "Runtime log: $runtimeLog" "ClaudeMuted"
    Write-LaunchStatus "Error log: $errorLog" "ClaudeMuted"
    exit 0
}

Write-LaunchStatus "Entrando en modo vigilancia activa..." "ClaudePrimary"
& $pythonExe @args
