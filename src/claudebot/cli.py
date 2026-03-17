from __future__ import annotations

import argparse
from pathlib import Path

from .monitor import MonitorConfig, parse_hotkey, parse_region, run_monitor, save_window_capture


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='ClaudeBot: pulsa Ctrl+Enter cuando Claude Desktop pide confirmacion para continuar.'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    run_parser = subparsers.add_parser('run', help='Inicia el monitor visual y envia Ctrl+Enter cuando toca.')
    run_parser.add_argument('--window-title', default='Claude', help='Texto que debe aparecer en el titulo de la ventana.')
    run_parser.add_argument('--template', default='assets/claude_ctrl_enter_template.png', help='Plantilla PNG del CTA de Claude.')
    run_parser.add_argument('--threshold', type=float, default=0.92, help='Confianza minima de matchTemplate (0-1).')
    run_parser.add_argument('--interval', type=float, default=5.0, help='Segundos entre comprobaciones.')
    run_parser.add_argument('--cooldown', type=float, default=4.0, help='Segundos de espera tras cada disparo.')
    run_parser.add_argument('--region', help='Region relativa a la ventana con formato x,y,w,h.')
    run_parser.add_argument('--hotkey', default='ctrl,enter', help='Teclas a enviar separadas por comas.')
    run_parser.add_argument('--evidence-dir', default='evidence', help='Carpeta donde guardar capturas before/after al actuar.')
    run_parser.add_argument('--color', action='store_true', help='Usa match en color. Por defecto usa escala de grises.')
    run_parser.add_argument('--dry-run', action='store_true', help='Detecta el CTA pero no envia teclas.')

    capture_parser = subparsers.add_parser('capture', help='Guarda una captura de la ventana de Claude y termina.')
    capture_parser.add_argument('--window-title', default='Claude', help='Texto que debe aparecer en el titulo de la ventana.')
    capture_parser.add_argument('--region', help='Region relativa a la ventana con formato x,y,w,h.')
    capture_parser.add_argument('--output', required=True, help='Ruta donde guardar la captura PNG.')

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == 'capture':
        save_window_capture(args.window_title, Path(args.output), parse_region(args.region))
        return 0

    template_path = Path(args.template)
    if not template_path.exists():
        parser.error(f'No existe la plantilla: {template_path}')

    config = MonitorConfig(
        window_title=args.window_title,
        template_path=template_path,
        threshold=args.threshold,
        interval=args.interval,
        cooldown=args.cooldown,
        grayscale=not args.color,
        region=parse_region(args.region),
        hotkey=parse_hotkey(args.hotkey),
        evidence_dir=Path(args.evidence_dir),
        dry_run=args.dry_run,
    )
    run_monitor(config)
    return 0
