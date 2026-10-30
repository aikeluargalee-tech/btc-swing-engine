"""Rich terminal dashboard and console reporting for the BTC Swing Engine."""

from .terminal_hud import build_dashboard_renderable, print_dry_run_report, run_terminal_hud

__all__ = [
    "build_dashboard_renderable",
    "print_dry_run_report",
    "run_terminal_hud",
]
