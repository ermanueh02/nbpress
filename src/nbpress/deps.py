"""
Dependency management and verification for external requirements.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Optional
from rich.console import Console

SLIDE_PRINTER_GIT_URL = "git+https://github.com/ermanueh02/Slide-printer.git"


def ensure_slide_printer(console: Optional[Console] = None) -> bool:
    """
    Ensure slide-printer is installed in the current Python environment.
    If not found, automatically install the latest version from git.
    """
    try:
        import slide_printer  # noqa: F401
        return True
    except ImportError:
        c = console or Console(highlight=False)
        c.print("\n[bold yellow]⚡ slide-printer no está instalado en el entorno.[/bold yellow]")
        c.print(f"[cyan]📦 Descargando e instalando la última versión desde git ({SLIDE_PRINTER_GIT_URL})...[/cyan]")
        try:
            cmd = [sys.executable, "-m", "pip", "install", SLIDE_PRINTER_GIT_URL]
            subprocess.check_call(cmd)
            c.print("[bold green]✔ slide-printer instalado correctamente desde git.[/bold green]\n")
            return True
        except Exception as err:
            c.print(f"[bold red]❌ Error al instalar slide-printer desde git:[/bold red] {err}")
            return False
