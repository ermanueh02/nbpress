"""
Interactive terminal wizard for nbpress (Slide-Printer Wizard 4.2.0 style).
Guides the user step-by-step through discovering notebooks, configuring print geometry,
selecting layouts, inspecting cell contents, compiling via Typst, and viewing outputs.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from nbpress import __version__
from nbpress.config import LayoutMode, NbpressConfig, PaperSize
from nbpress.generator import generate_pdf
from nbpress.parser import load_notebook

console = Console(highlight=False)

WIZARD_BANNER = """[bold cyan]
███╗   ██╗██████╗ ██████╗ ██████╗ ███████╗███████╗███████╗
████╗  ██║██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔════╝
██╔██╗ ██║██████╔╝██████╔╝██████╔╝█████╗  ███████╗███████╗
██║╚██╗██║██╔══██╗██╔═══╝ ██╔══██╗██╔══╝  ╚════██║╚════██║
██║ ╚████║██████╔╝██║     ██║  ██║███████╗███████║███████║
╚═╝  ╚═══╝╚═════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝[/bold cyan]
   [bold yellow]★ SLIDE-PRINTER WIZARD v4.2.0 ★[/bold yellow]
   [dim]Motor editorial de impresión para Jupyter Notebooks | Typst Engine[/dim]
"""


def find_notebooks(search_dir: Path) -> List[Path]:
    """Search for .ipynb files in the given directory and immediate subdirectories."""
    found: List[Path] = []
    ignore_dirs = {".venv", "venv", ".git", ".ipynb_checkpoints", "__pycache__", "node_modules"}

    try:
        for p in search_dir.glob("*.ipynb"):
            if not any(part in ignore_dirs for part in p.parts):
                found.append(p)
        for p in search_dir.glob("*/*.ipynb"):
            if not any(part in ignore_dirs for part in p.parts):
                found.append(p)
    except Exception:
        pass

    # Sort by recent modification date
    found.sort(key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
    return found


def step_select_notebook(console: Console) -> Optional[Path]:
    """Step 1: Discover or prompt for the target .ipynb file."""
    console.print("\n[bold cyan]━━━ PASO 1: SELECCIÓN DEL CUADERNO JUPYTER ━━━[/bold cyan]")
    
    cwd = Path.cwd()
    available = find_notebooks(cwd)

    if available:
        table = Table(
            title="Cuadernos detectados en el directorio actual",
            border_style="cyan",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("#", justify="center", style="bold yellow", width=4)
        table.add_column("Archivo Notebook", style="white")
        table.add_column("Tamaño", justify="right", style="cyan", width=12)
        table.add_column("Ruta Relativa", style="dim")

        for idx, nb_file in enumerate(available[:12], start=1):
            try:
                rel_path = nb_file.relative_to(cwd)
            except ValueError:
                rel_path = nb_file
            size_kb = nb_file.stat().st_size / 1024
            table.add_row(
                str(idx),
                nb_file.name,
                f"{size_kb:.1f} KB",
                str(rel_path),
            )

        console.print(table)
        console.print(
            "[dim]Selecciona el número del cuaderno, pulsa [bold white]'m'[/bold white] para ruta manual, o [bold white]'q'[/bold white] para salir.[/dim]"
        )

        while True:
            choice = Prompt.ask(
                "[bold green]Elige una opción[/bold green]",
                default="1" if available else "m",
                console=console,
            ).strip()

            if choice.lower() in ("q", "quit", "exit"):
                return None

            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(available[:12]):
                    return available[num - 1]
                console.print("[red]Número fuera de rango. Inténtalo de nuevo.[/red]")
                continue

            if choice.lower() == "m":
                break

            # If user dragged and dropped a file path directly
            raw_path = choice.strip("'\"")
            candidate = Path(raw_path)
            if candidate.exists() and candidate.is_file():
                return candidate
            console.print("[red]Opción no reconocida o ruta inexistente.[/red]")

    # Manual path prompt
    while True:
        path_str = Prompt.ask(
            "[bold green]Introduce la ruta del archivo .ipynb[/bold green] (o arrástralo aquí)",
            console=console,
        ).strip().strip("'\"")

        if path_str.lower() in ("q", "quit", "exit"):
            return None

        path = Path(path_str)
        if path.exists() and path.is_file() and path.suffix.lower() == ".ipynb":
            return path
        console.print(f"[bold red]❌ Archivo no encontrado o no es .ipynb:[/bold red] {path_str}")


def step_inspect_notebook(notebook_path: Path, console: Console) -> tuple[str, Optional[str]]:
    """Step 2: Inspect notebook structure and configure title/author overrides."""
    console.print("\n[bold cyan]━━━ PASO 2: INSPECCIÓN Y METADATOS EDITORIALES ━━━[/bold cyan]")
    
    try:
        doc = load_notebook(notebook_path)
    except Exception as e:
        console.print(f"[bold red]Error al parsear el cuaderno:[/bold red] {e}")
        return notebook_path.stem, None

    total_cells = len(doc.cells)
    md_cells = sum(1 for c in doc.cells if c.cell_type.value == "markdown")
    code_cells = sum(1 for c in doc.cells if c.cell_type.value == "code")
    raw_cells = sum(1 for c in doc.cells if c.cell_type.value == "raw")

    total_images = sum(sum(1 for out in c.outputs if out.has_image) for c in doc.cells)
    total_tables = sum(sum(1 for out in c.outputs if out.has_html_table) for c in doc.cells)
    total_errors = sum(sum(1 for out in c.outputs if out.output_type.value == "error") for c in doc.cells)
    slides_count = sum(1 for c in doc.cells if c.is_slide_starter)

    info_table = Table(box=None, padding=(0, 2), show_header=False)
    info_table.add_column("Key", style="bold cyan", justify="right")
    info_table.add_column("Val", style="white")

    info_table.add_row("Título detectado:", f"[bold green]{doc.title}[/bold green]")
    authors_str = ", ".join(doc.authors) if doc.authors else "No detectado"
    info_table.add_row("Autor(es):", authors_str)
    info_table.add_row("Total de celdas:", f"{total_cells} (Markdown: {md_cells}, Código: {code_cells})")
    info_table.add_row("Elementos visuales:", f"Gráficos/Imágenes: [magenta]{total_images}[/magenta] | Tablas: [yellow]{total_tables}[/yellow]")
    if total_errors > 0:
        info_table.add_row("Alertas:", f"[bold red]{total_errors} celdas contienen errores de ejecución[/bold red]")
    if slides_count > 0:
        info_table.add_row("Diapositivas RISE:", f"[bold blue]{slides_count} secciones/diapositivas detectadas[/bold blue]")

    console.print(Panel(info_table, title=f"📊 Análisis de {notebook_path.name}", border_style="blue"))

    # Optional metadata override
    override_meta = Confirm.ask(
        "¿Deseas personalizar el título o autor para la portada/encabezado?",
        default=False,
        console=console,
    )
    final_title = doc.title
    final_author = ", ".join(doc.authors) if doc.authors else None

    if override_meta:
        custom_title = Prompt.ask(
            "[bold green]Título del documento[/bold green]",
            default=doc.title,
            console=console,
        ).strip()
        if custom_title:
            final_title = custom_title

        custom_author = Prompt.ask(
            "[bold green]Autor / Institución[/bold green]",
            default=final_author or "",
            console=console,
        ).strip()
        final_author = custom_author if custom_author else None

    return final_title, final_author


def step_select_layout(console: Console) -> LayoutMode:
    """Step 3: Select layout architecture."""
    console.print("\n[bold cyan]━━━ PASO 3: ARQUITECTURA Y MAQUETACIÓN ━━━[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta", border_style="cyan")
    table.add_column("#", justify="center", style="bold yellow", width=4)
    table.add_column("Modo de Maquetación", style="bold white", width=22)
    table.add_column("Descripción y Caso de Uso", style="dim")

    table.add_row(
        "1",
        "📄 Documento",
        "Informe continuo A4/Letter con portada editorial, tabla de contenidos (TOC), encabezados a doble cara y numeración.",
    )
    table.add_row(
        "2",
        "🖥️  Diapositivas 16:9",
        "Presentación apaisada tipo Beamer/Deck moderna. Cada sección o celda slide se formatea como diapositiva limpia.",
    )
    table.add_row(
        "3",
        "📝 Handout para Clase",
        "Formato apuntes: Diapositiva en la mitad superior y pauta de líneas/rejilla abajo para notas manuscritas.",
    )
    table.add_row(
        "4",
        "⚡ Cheatsheet",
        "Chuleta compacta en 2 columnas con márgenes mínimos. Máxima densidad de fórmulas y código para exámenes o repaso.",
    )

    console.print(table)

    choices = {
        "1": LayoutMode.DOCUMENT,
        "2": LayoutMode.SLIDES,
        "3": LayoutMode.HANDOUT,
        "4": LayoutMode.CHEATSHEET,
    }

    while True:
        sel = Prompt.ask(
            "[bold green]Elige el estilo de maquetación [1-4][/bold green]",
            default="1",
            choices=["1", "2", "3", "4"],
            console=console,
        )
        if sel in choices:
            return choices[sel]


def step_paper_and_eco(layout: LayoutMode, console: Console) -> tuple[PaperSize, bool, Optional[str]]:
    """Step 4: Configure paper size, ink-saving eco mode, and binding gutter."""
    console.print("\n[bold cyan]━━━ PASO 4: GEOMETRÍA DE IMPRESIÓN Y MODO ECO ━━━[/bold cyan]")

    # Paper selection
    if layout == LayoutMode.SLIDES:
        paper = PaperSize.PRESENTATION_16_9
        console.print("[dim]Tamaño de papel fijado automáticamente a Presentation 16:9 para diapositivas.[/dim]")
    else:
        table = Table(box=None, show_header=False)
        table.add_column("#", style="bold yellow", width=4)
        table.add_column("Formato", style="bold white", width=14)
        table.add_column("Dimensiones", style="dim")
        table.add_row("1", "A4", "210 x 297 mm (Estándar internacional de apuntes y libros)")
        table.add_row("2", "US Letter", "8.5 x 11 in (Estándar norteamericano)")
        table.add_row("3", "A5", "148 x 210 mm (Formato bolsillo / libreta)")
        console.print(table)

        paper_choice = Prompt.ask(
            "[bold green]Formato de papel [1-3][/bold green]",
            default="1",
            choices=["1", "2", "3"],
            console=console,
        )
        paper_map = {
            "1": PaperSize.A4,
            "2": PaperSize.LETTER,
            "3": PaperSize.A5,
        }
        paper = paper_map[paper_choice]

    # Eco mode
    eco = Confirm.ask(
        "¿Activar modo ECO (ahorro de tinta y tóner con fondos blancos y bordes finos)?",
        default=False,
        console=console,
    )

    # Binding gutter
    gutter: Optional[str] = None
    if layout in (LayoutMode.DOCUMENT, LayoutMode.HANDOUT):
        console.print("\n[bold]Margen de encuadernación (Gutter para espiral / canutillo):[/bold]")
        console.print("  [bold yellow]1[/bold yellow] - Sin margen extra (0 cm)")
        console.print("  [bold yellow]2[/bold yellow] - Encuadernación con espiral estándar (1.0 cm)")
        console.print("  [bold yellow]3[/bold yellow] - Carpeta de anillas ancha (1.5 cm)")
        console.print("  [bold yellow]4[/bold yellow] - Personalizado")

        gutter_choice = Prompt.ask(
            "[bold green]Margen de lomo [1-4][/bold green]",
            default="1",
            choices=["1", "2", "3", "4"],
            console=console,
        )
        if gutter_choice == "2":
            gutter = "1.0cm"
        elif gutter_choice == "3":
            gutter = "1.5cm"
        elif gutter_choice == "4":
            custom_gutter = Prompt.ask(
                "[bold green]Introduce el margen con unidad (ej: 0.8cm, 1.2cm)[/bold green]",
                default="1.2cm",
                console=console,
            ).strip()
            gutter = custom_gutter if custom_gutter else None

    return paper, eco, gutter


def step_fine_tuning(
    notebook_path: Path,
    layout: LayoutMode,
    console: Console,
) -> tuple[bool, bool, int, bool, bool, Path, bool]:
    """Step 5: Fine tuning options (code display, TOC, cover, output path)."""
    console.print("\n[bold cyan]━━━ PASO 5: AJUSTES DE CONTENIDO Y SALIDA ━━━[/bold cyan]")

    show_code = Confirm.ask(
        "¿Incluir las celdas de código fuente?",
        default=True,
        console=console,
    )

    line_numbers = True
    if show_code:
        line_numbers = Confirm.ask(
            "¿Mostrar números de línea en los bloques de código?",
            default=True,
            console=console,
        )

    handout_lines = 8
    if layout == LayoutMode.HANDOUT:
        handout_lines = IntPrompt.ask(
            "[bold green]Número de líneas pautadas para notas manuscritas[/bold green]",
            default=8,
            console=console,
        )

    cover = True
    toc = True
    if layout == LayoutMode.DOCUMENT:
        cover = Confirm.ask(
            "¿Incluir portada editorial con título y metadatos?",
            default=True,
            console=console,
        )
        toc = Confirm.ask(
            "¿Generar tabla de contenidos (Índice interactivo)?",
            default=True,
            console=console,
        )

    # Suggest intelligent suffix
    suffix_map = {
        LayoutMode.DOCUMENT: ".pdf",
        LayoutMode.SLIDES: "_slides.pdf",
        LayoutMode.HANDOUT: "_handout.pdf",
        LayoutMode.CHEATSHEET: "_cheatsheet.pdf",
    }
    default_out_name = notebook_path.stem + suffix_map.get(layout, ".pdf")
    default_out_path = notebook_path.parent / default_out_name

    out_str = Prompt.ask(
        "[bold green]Ruta del archivo PDF de salida[/bold green]",
        default=str(default_out_path),
        console=console,
    ).strip().strip("'\"")
    output_path = Path(out_str)
    if not output_path.suffix:
        output_path = output_path.with_suffix(".pdf")

    keep_typ = Confirm.ask(
        "¿Guardar también el código fuente de Typst (.typ) para edición avanzada?",
        default=False,
        console=console,
    )

    return show_code, line_numbers, handout_lines, cover, toc, output_path, keep_typ


def step_manifest_and_compile(
    notebook_path: Path,
    output_path: Path,
    config: NbpressConfig,
    keep_typ: bool,
    console: Console,
) -> Optional[Path]:
    """Step 6 & 7: Display pre-flight manifest and execute Typst compilation."""
    console.print("\n[bold cyan]━━━ PASO 6: MANIFIESTO DE COMPILACIÓN ━━━[/bold cyan]")

    manifest = Table(border_style="green", show_header=True, header_style="bold green")
    manifest.add_column("Parámetro", style="bold cyan", width=22)
    manifest.add_column("Configuración", style="white")

    manifest.add_row("Cuaderno de origen", str(notebook_path.name))
    manifest.add_row("Archivo de salida", str(output_path.name))
    manifest.add_row("Modo de maquetación", config.layout.value.upper())
    manifest.add_row("Formato de papel", config.paper.value.upper())
    manifest.add_row("Modo Ahorro ECO", "✔ Activado (B&W Friendly)" if config.eco else "✖ Desactivado (Color completo)")
    if config.gutter:
        manifest.add_row("Margen encuadernación", config.gutter)
    manifest.add_row("Código fuente", "Visible con numeración" if (config.show_code and config.line_numbers) else ("Visible" if config.show_code else "Oculto"))
    if config.layout == LayoutMode.DOCUMENT:
        manifest.add_row("Portada & Índice", f"Portada: {'Sí' if config.cover else 'No'} | TOC: {'Sí' if config.toc else 'No'}")
    elif config.layout == LayoutMode.HANDOUT:
        manifest.add_row("Pauta manuscrita", f"{config.handout_note_lines} líneas pautadas por diapositiva")

    console.print(Panel(manifest, title="⚙️ Resumen Pre-Vuelo", border_style="cyan"))

    ready = Confirm.ask(
        "[bold green]¿Proceder con la compilación?[/bold green]",
        default=True,
        console=console,
    )
    if not ready:
        console.print("[yellow]Compilación abortada por el usuario.[/yellow]")
        return None

    console.print("\n[bold cyan]━━━ PASO 7: COMPILANDO CON TYPST NATIVO ━━━[/bold cyan]")

    with console.status("[bold blue]Transformando Markdown, LaTeX, gráficos y tablas con Typst...[/bold blue]"):
        try:
            pdf_path, duration = generate_pdf(
                notebook_path=notebook_path,
                output_pdf_path=output_path,
                config=config,
                keep_typ_source=keep_typ,
            )
        except Exception as e:
            console.print(f"[bold red]❌ Error durante la generación del PDF:[/bold red] {e}")
            return None

    file_size_kb = pdf_path.stat().st_size / 1024
    success_text = Text()
    success_text.append("✔ Documento generado exitosamente\n", style="bold green")
    success_text.append(f"• Destino: {pdf_path.resolve()}\n", style="bold white")
    success_text.append(f"• Tamaño: {file_size_kb:.1f} KB\n", style="cyan")
    success_text.append(f"• Tiempo de compilación: {duration * 1000:.0f} ms\n", style="yellow")
    if keep_typ:
        success_text.append(f"• Fuente Typst: {pdf_path.with_suffix('.typ').resolve()}\n", style="dim")

    console.print(Panel(success_text, title="🎉 Compilación Finalizada", border_style="green"))
    return pdf_path


def step_post_action(pdf_path: Path, console: Console) -> str:
    """Step 8: Post-generation menu."""
    console.print("\n[bold cyan]━━━ PASO 8: ACCIONES POST-GENERACIÓN ━━━[/bold cyan]")
    console.print("  [bold yellow]1[/bold yellow] - 🚀 Abrir PDF ahora (Visor predeterminado)")
    console.print("  [bold yellow]2[/bold yellow] - 📁 Mostrar archivo en el Explorador")
    console.print("  [bold yellow]3[/bold yellow] - 🔄 Compilar otro cuaderno con el asistente")
    console.print("  [bold yellow]4[/bold yellow] - 🚪 Salir")

    action = Prompt.ask(
        "[bold green]Elige una acción [1-4][/bold green]",
        default="1",
        choices=["1", "2", "3", "4"],
        console=console,
    )

    if action == "1":
        try:
            if sys.platform == "win32":
                os.startfile(str(pdf_path.resolve()))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(pdf_path.resolve())], check=False)
            else:
                subprocess.run(["xdg-open", str(pdf_path.resolve())], check=False)
            console.print("[green]✔ Visor de documentos abierto.[/green]")
        except Exception as e:
            console.print(f"[yellow]No se pudo abrir el visor automáticamente:[/yellow] {e}")
        return "exit"
    elif action == "2":
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", f"/select,{pdf_path.resolve()}"], check=False)
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", str(pdf_path.resolve())], check=False)
            else:
                subprocess.run(["xdg-open", str(pdf_path.parent.resolve())], check=False)
            console.print("[green]✔ Carpeta abierta en el explorador de archivos.[/green]")
        except Exception as e:
            console.print(f"[yellow]No se pudo abrir el explorador:[/yellow] {e}")
        return "exit"
    elif action == "3":
        return "again"
    else:
        return "exit"


def run_wizard(custom_console: Optional[Console] = None) -> None:
    """Main entrypoint for the interactive slide-printer wizard."""
    c = custom_console or console

    while True:
        try:
            if hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
                c.clear()
        except Exception:
            pass

        c.print(Align.center(WIZARD_BANNER))

        try:
            notebook_path = step_select_notebook(c)
            if not notebook_path:
                c.print("\n[yellow]Asistente finalizado sin cambios. ¡Hasta luego![/yellow]")
                break

            title, author = step_inspect_notebook(notebook_path, c)
            layout = step_select_layout(c)
            paper, eco, gutter = step_paper_and_eco(layout, c)
            show_code, line_numbers, handout_lines, cover, toc, output_path, keep_typ = step_fine_tuning(
                notebook_path, layout, c
            )

            config = NbpressConfig(
                layout=layout,
                paper=paper,
                eco=eco,
                gutter=gutter,
                cover=cover,
                toc=toc,
                show_code=show_code,
                line_numbers=line_numbers,
                handout_note_lines=handout_lines,
                title_override=title,
                author_override=author,
            )

            pdf_path = step_manifest_and_compile(
                notebook_path=notebook_path,
                output_path=output_path,
                config=config,
                keep_typ=keep_typ,
                console=c,
            )

            if pdf_path and pdf_path.exists():
                action = step_post_action(pdf_path, c)
                if action == "again":
                    continue
            break

        except (KeyboardInterrupt, EOFError):
            c.print("\n\n[yellow]Operación cancelada por el usuario. ¡Hasta la próxima![/yellow]")
            break
        except Exception as e:
            c.print(f"\n[bold red]Error inesperado en el asistente:[/bold red] {e}")
            break
