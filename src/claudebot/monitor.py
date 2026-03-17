from __future__ import annotations

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
    dry_run: bool


def log(message: str) -> None:
    stamp = datetime.now().strftime('%H:%M:%S')
    try:
        print(f'[{stamp}] {message}', flush=True)
    except OSError:
        pass


def find_window(title_hint: str):
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


def focus_window(window) -> None:
    if window.isMinimized:
        window.restore()
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
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), capture)
    log(f'Captura guardada en {output}')


def run_monitor(config: MonitorConfig) -> None:
    template = load_template(config.template_path, grayscale=config.grayscale)
    last_triggered = 0.0
    action_label = '+'.join(config.hotkey)
    log(f"Monitorizando la ventana '{config.window_title}' usando {config.template_path} y accion {action_label}")

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
                        log(f'Coincidencia detectada ({confirm_score:.3f}) en x={confirm_location[0]}, y={confirm_location[1]}')
                        if not config.dry_run:
                            trigger_hotkey(window, config.hotkey)
                            log(f"Hotkey enviada: {'+'.join(config.hotkey)}")
                        else:
                            log('Dry run activo: no se envio ninguna tecla')
                        last_triggered = now
                    else:
                        log(f'Coincidencia descartada ({score:.3f}) en x={location[0]}, y={location[1]}')
            else:
                log('No he encontrado una solicitud de continuacion, sigo vigilando')
            time.sleep(config.interval)
        except KeyboardInterrupt:
            log('Bot detenido por el usuario')
            return
        except Exception as exc:
            log(f'Esperando ventana o plantilla valida: {exc}')
            time.sleep(max(config.interval, 1.0))
