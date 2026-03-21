from __future__ import annotations

import platform
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pyautogui


pyautogui.FAILSAFE = True
LOWER_ZONE_RATIO = 0.6
CONFIRMATION_DELAY = 0.35


@dataclass(frozen=True)
class MonitorConfig:
    window_title: str
    template_path: Path
    threshold: float
    interval: float
    cooldown: float
    grayscale: bool
    region: Optional[tuple[int, int, int, int]]
    hotkey: tuple[str, ...]
    evidence_dir: Path
    mouse_idle_seconds: float
    dry_run: bool


@dataclass
class MacOSWindow:
    app_name: str
    title: str
    left: int
    top: int
    width: int
    height: int
    isMinimized: bool = False

    def restore(self) -> None:
        return

    def activate(self) -> None:
        activate_macos_app(self.app_name)


def log(message: str) -> None:
    stamp = datetime.now().strftime('%H:%M:%S')
    try:
        print(f'[{stamp}] {message}', flush=True)
    except OSError:
        pass


def log_state(label: str, message: str) -> None:
    log(f'{label:<10} {message}')


def log_intervention(message: str) -> None:
    log('----------------------------------------')
    log_state('CLAUDEBOT', message)
    log('----------------------------------------')


def run_osascript(script: str) -> str:
    result = subprocess.run(
        ['osascript', '-e', script],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def activate_macos_app(app_name: str) -> None:
    escaped = app_name.replace('"', '\"')
    run_osascript(f'tell application "{escaped}" to activate')


def find_window_macos(title_hint: str) -> MacOSWindow:
    escaped_hint = title_hint.replace('"', '\"')
    script = f'''
        tell application "System Events"
            set matchingProcesses to every application process whose background only is false and name contains "{escaped_hint}"
            if (count of matchingProcesses) is 0 then
                error "No encuentro una app con el nombre {escaped_hint}"
            end if
            set targetProcess to item 1 of matchingProcesses
            set targetName to name of targetProcess
            if (count of windows of targetProcess) is 0 then
                error "La app {escaped_hint} no tiene ventanas visibles"
            end if
            set targetWindow to item 1 of windows of targetProcess
            set targetTitle to name of targetWindow
            set {{xPos, yPos}} to position of targetWindow
            set {{winWidth, winHeight}} to size of targetWindow
            return targetName & "||" & targetTitle & "||" & xPos & "||" & yPos & "||" & winWidth & "||" & winHeight
        end tell
    '''
    raw = run_osascript(script)
    parts = raw.split('||')
    if len(parts) != 6:
        raise RuntimeError(f'Respuesta inesperada de macOS al buscar la ventana: {raw}')
    app_name, window_title, left, top, width, height = parts
    return MacOSWindow(
        app_name=app_name,
        title=window_title,
        left=int(left),
        top=int(top),
        width=int(width),
        height=int(height),
    )


def find_window(title_hint: str):
    if platform.system() == 'Darwin':
        return find_window_macos(title_hint)

    matches = [window for window in pyautogui.getWindowsWithTitle(title_hint) if window.title]
    if not matches:
        raise RuntimeError(f"No encuentro una ventana con el titulo que contenga '{title_hint}'.")
    return matches[0]


def normalize_region(window, region: Optional[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    left = max(int(window.left), 0)
    top = max(int(window.top), 0)
    width = max(int(window.width), 1)
    height = max(int(window.height), 1)
    if region is None:
        return left, top, width, height

    rel_x, rel_y, rel_w, rel_h = region
    abs_left = max(left + rel_x, left)
    abs_top = max(top + rel_y, top)
    abs_right = min(left + rel_x + rel_w, left + width)
    abs_bottom = min(top + rel_y + rel_h, top + height)
    return abs_left, abs_top, max(abs_right - abs_left, 1), max(abs_bottom - abs_top, 1)


def screenshot_region(region: tuple[int, int, int, int]) -> np.ndarray:
    shot = pyautogui.screenshot(region=region)
    frame = np.array(shot)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


def save_frame(frame: np.ndarray, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), frame)


def load_template(path: Path, grayscale: bool) -> np.ndarray:
    flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    template = cv2.imread(str(path), flag)
    if template is None:
        raise RuntimeError(f'No pude leer la plantilla: {path}')
    return template


def match_template(frame: np.ndarray, template: np.ndarray, grayscale: bool) -> tuple[float, tuple[int, int]]:
    haystack = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if grayscale else frame
    result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return float(max_val), (int(max_loc[0]), int(max_loc[1]))


def detection_is_actionable(
    frame: np.ndarray,
    template: np.ndarray,
    grayscale: bool,
    threshold: float,
) -> tuple[bool, float, tuple[int, int], tuple[int, int]]:
    score, location = match_template(frame, template, grayscale=grayscale)
    lower_limit = int(frame.shape[0] * LOWER_ZONE_RATIO)
    is_low_enough = location[1] >= lower_limit
    size = (int(template.shape[1]), int(template.shape[0]))
    return score >= threshold and is_low_enough, score, location, size


def get_mouse_position() -> tuple[int, int]:
    point = pyautogui.position()
    return int(point.x), int(point.y)


def wait_for_mouse_idle(idle_seconds: float, poll_interval: float = 0.2) -> None:
    if idle_seconds <= 0:
        return

    last_position = get_mouse_position()
    last_moved_at = time.time()
    waiting_logged = False

    while True:
        time.sleep(poll_interval)
        current_position = get_mouse_position()
        now = time.time()
        if current_position != last_position:
            last_position = current_position
            last_moved_at = now
            waiting_logged = False
            continue

        idle_for = now - last_moved_at
        if idle_for >= idle_seconds:
            return

        if not waiting_logged:
            remaining = idle_seconds - idle_for
            log(f'Ratón en movimiento reciente; espero {remaining:.1f}s de quietud antes de cambiar la ventana')
            waiting_logged = True


def focus_window(window) -> None:
    if getattr(window, 'isMinimized', False):
        restore = getattr(window, 'restore', None)
        if callable(restore):
            restore()
            time.sleep(0.2)
    window.activate()
    time.sleep(0.15)


def trigger_hotkey(window, hotkey: tuple[str, ...]) -> None:
    focus_window(window)
    pyautogui.hotkey(*hotkey)


def parse_region(raw: Optional[str]) -> Optional[tuple[int, int, int, int]]:
    if not raw:
        return None
    parts = [int(part.strip()) for part in raw.split(',')]
    if len(parts) != 4:
        raise ValueError('--region debe tener el formato x,y,w,h')
    return parts[0], parts[1], parts[2], parts[3]


def parse_hotkey(raw: str) -> tuple[str, ...]:
    keys = tuple(part.strip() for part in raw.split(',') if part.strip())
    if not keys:
        raise ValueError('--hotkey debe tener al menos una tecla, por ejemplo ctrl,enter')
    return keys


def save_window_capture(window_title: str, output: Path, region: Optional[tuple[int, int, int, int]]) -> None:
    window = find_window(window_title)
    focus_window(window)
    capture = screenshot_region(normalize_region(window, region))
    save_frame(capture, output)
    log(f'Captura guardada en {output}')


def capture_evidence(config: MonitorConfig, frame: np.ndarray, suffix: str) -> Path:
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    output = config.evidence_dir / f'claudebot_{stamp}_{suffix}.png'
    save_frame(frame, output)
    return output


def run_monitor(config: MonitorConfig) -> None:
    template = load_template(config.template_path, grayscale=config.grayscale)
    last_triggered = 0.0
    action_label = '+'.join(config.hotkey)
    platform_name = platform.system()
    log_state(
        'START',
        f"Monitorizando '{config.window_title}' en {platform_name} con plantilla {config.template_path} y accion {action_label}"
    )

    while True:
        try:
            window = find_window(config.window_title)
            capture = screenshot_region(normalize_region(window, config.region))
            actionable, score, location, _ = detection_is_actionable(
                capture,
                template,
                grayscale=config.grayscale,
                threshold=config.threshold,
            )
            if actionable:
                now = time.time()
                if now - last_triggered >= config.cooldown:
                    time.sleep(CONFIRMATION_DELAY)
                    confirm_capture = screenshot_region(normalize_region(window, config.region))
                    confirmed, confirm_score, confirm_location, _ = detection_is_actionable(
                        confirm_capture,
                        template,
                        grayscale=config.grayscale,
                        threshold=config.threshold,
                    )
                    if confirmed:
                        log_intervention(
                            f'Intervencion detectada ({confirm_score:.3f}) en x={confirm_location[0]}, y={confirm_location[1]}'
                        )
                        before_path = capture_evidence(config, confirm_capture, 'before')
                        log_state('EVIDENCE', f'Captura guardada antes de actuar: {before_path}')
                        if not config.dry_run:
                            wait_for_mouse_idle(config.mouse_idle_seconds)
                            window = find_window(config.window_title)
                            ready_capture = screenshot_region(normalize_region(window, config.region))
                            still_confirmed, ready_score, ready_location, _ = detection_is_actionable(
                                ready_capture,
                                template,
                                grayscale=config.grayscale,
                                threshold=config.threshold,
                            )
                            if not still_confirmed:
                                log_state(
                                    'CANCEL',
                                    f'Coincidencia cancelada tras esperar al ratón ({ready_score:.3f}) en x={ready_location[0]}, y={ready_location[1]}'
                                )
                                time.sleep(config.interval)
                                continue
                            trigger_hotkey(window, config.hotkey)
                            log_state('ACTION', f"Hotkey enviada: {'+'.join(config.hotkey)}")
                            time.sleep(0.5)
                            after_window = find_window(config.window_title)
                            after_capture = screenshot_region(normalize_region(after_window, config.region))
                            after_path = capture_evidence(config, after_capture, 'after')
                            log_state('EVIDENCE', f'Captura guardada despues de actuar: {after_path}')
                        else:
                            log_state('DRY-RUN', 'No se envio ninguna tecla')
                        last_triggered = now
                    else:
                        log_state('DISCARD', f'Coincidencia descartada ({score:.3f}) en x={location[0]}, y={location[1]}')
                else:
                    remaining = config.cooldown - (now - last_triggered)
                    log_state('COOLDOWN', f'Coincidencia detectada pero en enfriamiento ({remaining:.1f}s)')
            else:
                log_state('WATCHING', 'No he encontrado una solicitud de continuacion, sigo vigilando')
            time.sleep(config.interval)
        except KeyboardInterrupt:
            log_state('STOP', 'Bot detenido por el usuario')
            return
        except Exception as exc:
            log_state('WAIT', f'Esperando ventana o plantilla valida: {exc}')
            time.sleep(max(config.interval, 1.0))
