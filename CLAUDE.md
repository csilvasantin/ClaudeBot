# Proyecto 20 — ClaudeBot

> Bot que automatiza interacciones con Claude Desktop detectando CTAs visuales y pulsando hotkeys

## Contexto

ClaudeBot vigila la ventana de Claude Desktop, detecta cuando aparece un CTA visual que indica que Claude necesita confirmación, y automáticamente enfoca Claude y pulsa el hotkey configurado (por defecto `Ctrl+Enter` en Windows, `Command+Enter` en macOS). Guarda evidencia (capturas before/after) en `evidence/` para auditoria.

## Arquitectura

- **Detección**: OpenCV busca plantilla de CTA en captura de ventana de Claude
- **Activación**: Si detecta CTA, espera 5 segundos de quietud de ratón (para no interferir)
- **Acción**: Enfoca ventana de Claude, envía hotkey, guarda capturas
- **Ejecución**:
  - Windows: `python -m claudebot run` o `.run_claudebot.ps1` o `.\Launch.ps1` (watcher automático)
  - macOS: `./run_claudebot_mac.command` o con hotkey custom: `./run_claudebot_mac.command --hotkey command,enter`

## Stack

- Python 3, OpenCV, pygetwindow/AppleScript, pynput
- Windows PS1 scripts para lanzadores rápidos
- macOS `.command` scripts para ejecución desde Finder

## Notas para IAs

1. **Onboarding**: Leer `onboarding` antes de cambiar automatizaciones
2. **Plantilla CTA**: `assets/claude_ctrl_enter_template.png` define qué busca; si el botón cambia, reemplazar plantilla
3. **Opciones útiles**:
   - `--interval 3`: Chequear cada 3 segundos (default: depende de config)
   - `--threshold 0.9`: Sensibilidad de matching (0-1)
   - `--region 900,1500,800,500`: Monitorear solo región específica de pantalla
   - `--mouse-idle-seconds 8`: Esperar 8 segundos de quietud (default: 5)
   - `--dry-run`: Probar sin enviar teclas
4. **Evidencia**: Cada acción guarda `before.png` y `after.png` en `evidence/` para revisar comportamiento
5. **Permisos macOS**: Requiere `Accessibility` y `Screen Recording` en Terminal/iTerm/Python app
6. **Cierre de sesión**: Generar HTML con evidencia y URL pública verificable
7. **Terminal visible**: A diferencia de CodexBot, la consola está visible; banner ASCII al arrancar, mensajes periódicos de chequeo
