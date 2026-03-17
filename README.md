# ClaudeBot

ClaudeBot vigila la ventana de Claude Desktop y pulsa `Ctrl+Enter` cuando aparece el CTA visual que indica que Claude necesita confirmacion para continuar.

## Que hace

- Localiza la ventana cuyo titulo contiene `Claude`.
- Captura la zona visible o una region concreta.
- Busca una plantilla del boton de confirmacion mediante OpenCV.
- Si la coincidencia supera el umbral, enfoca la ventana y envia `Ctrl+Enter`.
- Aplica un `cooldown` para no repetir la accion varias veces seguidas.

## Instalacion

```powershell
cd 'H:\Mi unidad\Codex\ClaudeBot'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

```powershell
cd 'H:\Mi unidad\Codex\ClaudeBot'
$env:PYTHONPATH='H:\Mi unidad\Codex\ClaudeBot\src'
python -m claudebot run
```

Tambien puedes arrancarlo con:

```powershell
.\run_claudebot.ps1
```

Opciones utiles:

```powershell
python -m claudebot run --interval 3 --threshold 0.9
python -m claudebot run --region 900,1500,800,500
python -m claudebot run --template assets\claude_ctrl_enter_template.png
python -m claudebot capture --output debug\claude_window.png
```

## Estructura

- `src/claudebot/cli.py`: entrada principal.
- `src/claudebot/monitor.py`: detector visual y automatizacion de teclado.
- `assets/claude_ctrl_enter_template.png`: plantilla por defecto del CTA.

## Notas

- Claude Desktop debe estar visible en el escritorio del usuario.
- Si el aspecto del boton cambia, captura una nueva imagen y sustituye la plantilla en `assets/`.
- Si quieres probar sin enviar teclas, usa `--dry-run`.
