# ClaudeBot

ClaudeBot vigila la ventana de Claude Desktop y pulsa `Ctrl+Enter` cuando aparece el CTA visual que indica que Claude necesita confirmacion para continuar. Funciona en Windows y ahora incluye una ruta especifica para macOS.

## Que hace

- Localiza la ventana de Claude.
- Captura la ventana completa o una region concreta.
- Detecta el CTA visual con OpenCV.
- Enfoca Claude y envia la hotkey configurada.
- Si detecta movimiento reciente del raton, espera 5 segundos de quietud antes de cambiar de ventana.
- Guarda capturas `before` y `after` en `evidence/` cada vez que actua.

## Instalacion Windows

```powershell
cd 'H:\Mi unidad\Codex\ClaudeBot'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Instalacion macOS

```bash
cd /ruta/a/ClaudeBot
python3 -m venv .venv-mac
source .venv-mac/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Uso Windows

```powershell
cd 'H:\Mi unidad\Codex\ClaudeBot'
python -m claudebot run
```

O con el lanzador en primer plano:

```powershell
.\run_claudebot.ps1
```

O en segundo plano:

```powershell
.\run_claudebot.ps1 -Background
```

O con watcher automatico estilo CodexBot:

```powershell
.\Launch.ps1
```

Ese watcher arranca ClaudeBot cuando detecta la ventana de Claude y lo detiene cuando Claude se cierra.

## Uso macOS

```bash
chmod +x ./run_claudebot_mac.command
./run_claudebot_mac.command
```

Si en tu Claude para Mac el atajo correcto es `Command+Enter`, usa:

```bash
./run_claudebot_mac.command --hotkey command,enter
```

## Opciones utiles

```powershell
python -m claudebot run --interval 3 --threshold 0.9
python -m claudebot run --region 900,1500,800,500
python -m claudebot run --template assets\claude_ctrl_enter_template.png
python -m claudebot run --mouse-idle-seconds 8
python -m claudebot capture --output debug\claude_window.png
```

## Estructura

- `src/claudebot/cli.py`: entrada principal.
- `src/claudebot/monitor.py`: detector visual y automatizacion de teclado.
- `assets/claude_ctrl_enter_template.png`: plantilla por defecto del CTA.
- `evidence/`: capturas before/after que ClaudeBot guarda cada vez que actua.
- `run_claudebot.ps1`: lanzador rapido para Windows.
- `Launch.ps1`: arranca el watcher de Windows.
- `ClaudeBot-Watcher.ps1`: enciende y apaga ClaudeBot segun el estado de Claude.
- `run_claudebot_mac.command`: lanzador rapido para macOS.

## Notas

- Claude Desktop debe estar visible en el escritorio del usuario.
- En macOS hay que dar permisos de `Accessibility` y `Screen Recording` a Terminal, iTerm o a la app que ejecute Python.
- En macOS la deteccion de ventana usa AppleScript sobre `System Events`.
- Si el aspecto del boton cambia, sustituye la plantilla en `assets/`.
- Si quieres probar sin enviar teclas, usa `--dry-run`.
- Puedes ajustar la espera de quietud del raton con `--mouse-idle-seconds`; por defecto usa `5`.

## Arranque Rapido

- Windows: abre `START_WINDOWS.md` o haz doble clic en `run_claudebot.bat` para arrancar el watcher que sigue el ciclo de vida de Claude.
- macOS: abre `START_MAC.md` y ejecuta `./run_claudebot_mac.command`.
