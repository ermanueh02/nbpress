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
from nbpress.config import (
    DocTheme,
    HandoutDisposition,
    HandoutNoteStyle,
    LayoutMode,
    NbpressConfig,
    PaperSize,
)
from nbpress.generator import generate_multiple_pdfs, generate_pdf
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


def step_select_layout(console: Console) -> List[LayoutMode]:
    """Step 3: Select layout architecture(s)."""
    console.print("\n[bold cyan]━━━ PASO 3: ARQUITECTURA Y MAQUETACIÓN ━━━[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta", border_style="cyan")
    table.add_column("#", justify="center", style="bold yellow", width=4)
    table.add_column("Modo de Maquetación", style="bold white", width=22)
    table.add_column("Descripción y Caso de Uso", style="dim")

    table.add_row(
        "1",
        "📄 Documento",
        "Informe continuo A4/Letter con portada editorial, tabla de contenidos (TOC), encabezados y numeración.",
    )
    table.add_row(
        "2",
        "🖥️  Diapositivas 16:9",
        "Presentación apaisada tipo Beamer/Deck moderna. Cada sección o celda slide se formatea como diapositiva limpia.",
    )
    table.add_row(
        "3",
        "📝 Handout para Clase",
        "Slide-Printer: Diapositivas con área para notas (pauta, cuadrícula, bullet points o blanco).",
    )
    table.add_row(
        "4",
        "⚡ Cheatsheet",
        "Chuleta compacta en 2 columnas con márgenes mínimos. Máxima densidad de fórmulas y código para repaso.",
    )
    table.add_row(
        "5",
        "🌟 Todas las opciones",
        "Compilar simultáneamente las 4 maquetaciones para este documento (Documento, Slides, Handout y Cheatsheet).",
    )

    console.print(table)
    console.print("[dim]Puedes elegir una opción [1-5] o varias separadas por coma (ej: 1,3)[/dim]")

    choices_map = {
        "1": LayoutMode.DOCUMENT,
        "2": LayoutMode.SLIDES,
        "3": LayoutMode.HANDOUT,
        "4": LayoutMode.CHEATSHEET,
    }

    while True:
        sel = Prompt.ask(
            "[bold green]Elige la(s) maquetación(es) [1-5][/bold green]",
            default="1",
            console=console,
        ).strip().lower()

        if sel in ("5", "all", "todas", "todos", "*"):
            return [LayoutMode.DOCUMENT, LayoutMode.SLIDES, LayoutMode.HANDOUT, LayoutMode.CHEATSHEET]

        parts = [p.strip() for p in sel.split(",") if p.strip()]
        selected = []
        for p in parts:
            if p in choices_map and choices_map[p] not in selected:
                selected.append(choices_map[p])
        
        if selected:
            return selected
        console.print("[red]Opción no válida. Introduce un número del 1 al 5 o combinaciones como 1,2.[/red]")


def step_select_theme(console: Console) -> DocTheme:
    """Step 3.5: Select visual design theme / architecture."""
    console.print("\n[bold cyan]━━━ PASO 3.5: DISEÑO Y TEMA EDITORIAL ━━━[/bold cyan]")

    table = Table(show_header=True, header_style="bold magenta", border_style="cyan")
    table.add_column("#", justify="center", style="bold yellow", width=4)
    table.add_column("Tema Visual", style="bold white", width=24)
    table.add_column("Paleta y Estilo", style="dim")

    table.add_row(
        "1",
        "🏛️ Clásico Editorial",
        "Azul institucional, tipografía serif académica (Linux Libertine), estética formal y sobria.",
    )
    table.add_row(
        "2",
        "🎨 Mid-Century Modern",
        "Estética años 50-60: Mostaza ocre, terracota, verde oliva, fondo marfil cálido, tipografía geométrica y detalles retro.",
    )

    console.print(table)

    theme_choice = Prompt.ask(
        "[bold green]Elige el tema de diseño [1-2][/bold green]",
        default="1",
        choices=["1", "2"],
        console=console,
    )
    return DocTheme.MID_CENTURY if theme_choice == "2" else DocTheme.EDITORIAL


def step_paper_and_eco(layouts: List[LayoutMode], console: Console) -> tuple[PaperSize, bool, Optional[str]]:
    """Step 4: Configure paper size, ink-saving eco mode, and binding gutter."""
    console.print("\n[bold cyan]━━━ PASO 4: GEOMETRÍA DE IMPRESIÓN Y MODO ECO ━━━[/bold cyan]")

    # Paper selection
    if len(layouts) == 1 and layouts[0] == LayoutMode.SLIDES:
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
    if any(l in (LayoutMode.DOCUMENT, LayoutMode.HANDOUT) for l in layouts):
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
    layouts: List[LayoutMode],
    console: Console,
) -> tuple[bool, bool, HandoutNoteStyle, HandoutDisposition, bool, Optional[str], bool, bool, Path, bool]:
    """Step 5: Fine tuning options (code display, TOC, cover, slide-printer options, output path)."""
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

    # Handout specifics
    handout_note_style = HandoutNoteStyle.LINES
    handout_disposition = HandoutDisposition.ONE_UP
    study_header = False
    study_title: Optional[str] = None

    if LayoutMode.HANDOUT in layouts:
        console.print("\n[bold magenta]Configuración de Slide-Printer (Handouts):[/bold magenta]")
        console.print("  [bold yellow]1[/bold yellow] - ✍️  Líneas de pauta (Lined / caligrafía estándar)")
        console.print("  [bold yellow]2[/bold yellow] - 📐 Cuadrícula técnica (Grid / para fórmulas y gráficos)")
        console.print("  [bold yellow]3[/bold yellow] - ⏺️  Matriz de puntos / Bullet points (Dots)")
        console.print("  [bold yellow]4[/bold yellow] - 📄 Espacio en blanco (Blank)")

        style_choice = Prompt.ask(
            "[bold green]Estilo de área de notas [1-4][/bold green]",
            default="2",
            choices=["1", "2", "3", "4"],
            console=console,
        )
        style_map = {
            "1": HandoutNoteStyle.LINES,
            "2": HandoutNoteStyle.GRID,
            "3": HandoutNoteStyle.DOTS,
            "4": HandoutNoteStyle.BLANK,
        }
        handout_note_style = style_map[style_choice]

        disp_choice = Prompt.ask(
            "[bold green]Disposición de diapositivas [1=1-Up normal, 2=2-Up compacto][/bold green]",
            default="1",
            choices=["1", "2"],
            console=console,
        )
        handout_disposition = HandoutDisposition.TWO_UP if disp_choice == "2" else HandoutDisposition.ONE_UP

        study_header = Confirm.ask(
            "¿Incluir cabecera de estudio (Asignatura / Tema y Fecha para rellenar)?",
            default=False,
            console=console,
        )
        if study_header:
            custom_st = Prompt.ask(
                "[bold green]Título o tema para cabecera[/bold green]",
                default=notebook_path.stem.replace("_", " ").title(),
                console=console,
            ).strip()
            study_title = custom_st if custom_st else None

    cover = True
    toc = True
    if LayoutMode.DOCUMENT in layouts:
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

    # Suggest intelligent suffix or output path
    if len(layouts) > 1:
        default_out_path = notebook_path.parent
        console.print(f"[dim]Al compilar varias maquetaciones, se generarán PDFs con sufijos (_doc, _slides, etc.) en: {default_out_path}[/dim]")
        out_str = Prompt.ask(
            "[bold green]Directorio de salida[/bold green]",
            default=str(default_out_path),
            console=console,
        ).strip().strip("'\"")
        output_path = Path(out_str)
    else:
        suffix_map = {
            LayoutMode.DOCUMENT: ".pdf",
            LayoutMode.SLIDES: "_slides.pdf",
            LayoutMode.HANDOUT: "_handout.pdf",
            LayoutMode.CHEATSHEET: "_cheatsheet.pdf",
        }
        default_out_name = notebook_path.stem + suffix_map.get(layouts[0], ".pdf")
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

    return show_code, line_numbers, handout_note_style, handout_disposition, study_header, study_title, cover, toc, output_path, keep_typ


def step_manifest_and_compile(
    notebook_path: Path,
    output_path: Path,
    layouts: List[LayoutMode],
    config: NbpressConfig,
    keep_typ: bool,
    console: Console,
) -> List[Path]:
    """Step 6 & 7: Display pre-flight manifest and execute compilation."""
    console.print("\n[bold cyan]━━━ PASO 6: MANIFIESTO DE COMPILACIÓN ━━━[/bold cyan]")

    manifest = Table(border_style="green", show_header=True, header_style="bold green")
    manifest.add_column("Parámetro", style="bold cyan", width=22)
    manifest.add_column("Configuración", style="white")

    manifest.add_row("Cuaderno de origen", str(notebook_path.name))
    manifest.add_row("Maquetaciones elegidas", ", ".join(l.value.upper() for l in layouts))
    manifest.add_row("Tema y Diseño", config.theme.value.upper())
    manifest.add_row("Formato de papel", config.paper.value.upper())
    manifest.add_row("Modo Ahorro ECO", "✔ Activado (B&W Friendly)" if config.eco else "✖ Desactivado (Color completo)")
    if config.gutter:
        manifest.add_row("Margen encuadernación", config.gutter)
    manifest.add_row("Código fuente", "Visible con numeración" if (config.show_code and config.line_numbers) else ("Visible" if config.show_code else "Oculto"))

    if LayoutMode.HANDOUT in layouts:
        manifest.add_row("Slide-Printer Notas", f"Estilo: {config.handout_note_style.value.upper()} | Layout: {config.handout_disposition.value}")

    console.print(Panel(manifest, title="⚙️ Resumen Pre-Vuelo", border_style="cyan"))

    ready = Confirm.ask(
        "[bold green]¿Proceder con la compilación?[/bold green]",
        default=True,
        console=console,
    )
    if not ready:
        console.print("[yellow]Compilación abortada por el usuario.[/yellow]")
        return []

    console.print("\n[bold cyan]━━━ PASO 7: COMPILANDO CON MOTOR NBPRESS & SLIDE-PRINTER ━━━[/bold cyan]")

    generated_pdfs: List[Path] = []
    with console.status("[bold blue]Transformando Markdown, LaTeX, gráficos y diapositivas...[/bold blue]"):
        try:
            if len(layouts) > 1:
                out_dir = output_path if output_path.is_dir() else output_path.parent
                multi_res = generate_multiple_pdfs(
                    notebook_path=notebook_path,
                    layouts=layouts,
                    output_dir=out_dir,
                    config=config,
                    keep_typ_source=keep_typ,
                )
                generated_pdfs = [pdf for pdf, _ in multi_res.values()]
            else:
                target_pdf = output_path
                pdf_path, duration = generate_pdf(
                    notebook_path=notebook_path,
                    output_pdf_path=target_pdf,
                    config=config,
                    keep_typ_source=keep_typ,
                )
                generated_pdfs = [pdf_path]
        except Exception as e:
            console.print(f"[bold red]❌ Error durante la generación del PDF:[/bold red] {e}")
            return []

    success_table = Table(border_style="green", header_style="bold green")
    success_table.add_column("PDF Generado", style="bold white")
    success_table.add_column("Tamaño", justify="right", style="cyan")
    success_table.add_column("Ruta Completa", style="dim")

    for p in generated_pdfs:
        size_kb = p.stat().st_size / 1024 if p.exists() else 0
        success_table.add_row(p.name, f"{size_kb:.1f} KB", str(p.resolve()))

    console.print(Panel(success_table, title="🎉 Compilación Finalizada con Éxito", border_style="green"))
    return generated_pdfs


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
            layouts = step_select_layout(c)
            theme = step_select_theme(c)
            paper, eco, gutter = step_paper_and_eco(layouts, c)
            (
                show_code,
                line_numbers,
                handout_note_style,
                handout_disposition,
                study_header,
                study_title,
                cover,
                toc,
                output_path,
                keep_typ,
            ) = step_fine_tuning(notebook_path, layouts, c)

            config = NbpressConfig(
                layout=layouts[0],
                layouts=layouts,
                theme=theme,
                paper=paper,
                eco=eco,
                gutter=gutter,
                cover=cover,
                toc=toc,
                show_code=show_code,
                line_numbers=line_numbers,
                handout_note_style=handout_note_style,
                handout_disposition=handout_disposition,
                handout_study_header=study_header,
                handout_study_title=study_title,
                title_override=title,
                author_override=author,
            )

            pdf_paths = step_manifest_and_compile(
                notebook_path=notebook_path,
                output_path=output_path,
                layouts=layouts,
                config=config,
                keep_typ=keep_typ,
                console=c,
            )

            if pdf_paths and pdf_paths[0].exists():
                action = step_post_action(pdf_paths[0], c)
                if action == "again":
                    continue
            break

        except (KeyboardInterrupt, EOFError):
            c.print("\n\n[yellow]Operación cancelada por el usuario. ¡Hasta la próxima![/yellow]")
            break
        except Exception as e:
            c.print(f"\n[bold red]Error inesperado en el asistente:[/bold red] {e}")
            break
