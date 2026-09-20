"""
CLI interface for nbpress powered by Typer and Rich.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typst

# Force UTF-8 on Windows terminal streams to prevent UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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


app = typer.Typer(
    name="nbpress",
    help="Transform Jupyter Notebooks (.ipynb) into editorial-grade, print-ready PDFs.",
    no_args_is_help=False,
    add_completion=False,
)
console = Console(highlight=False)


def version_callback(value: bool):
    if value:
        typst_ver = getattr(typst, "__version__", "0.15.0")
        console.print(
            Panel(
                f"[bold cyan]nbpress[/bold cyan] versión [green]{__version__}[/green]\n"
                f"[bold cyan]Typst Engine[/bold cyan] versión [green]{typst_ver}[/green]",
                title="📖 Información de Versión",
                border_style="blue",
            )
        )
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Mostrar la versión de nbpress y el motor Typst.",
        callback=version_callback,
        is_eager=True,
    ),
    wizard: bool = typer.Option(
        False,
        "--wizard",
        "-w",
        help="Iniciar el asistente interactivo Slide-Printer Wizard 4.2.0",
    ),
):
    """
    Transforma cuadernos Jupyter (.ipynb) en documentos y diapositivas de alta calidad editorial.
    """
    from nbpress.deps import ensure_slide_printer
    ensure_slide_printer(console)

    if ctx.invoked_subcommand is None:
        from nbpress.wizard import run_wizard
        run_wizard()


@app.command(name="wizard")
def wizard_cmd():
    """Iniciar el asistente interactivo Slide-Printer Wizard 4.2.0."""
    from nbpress.deps import ensure_slide_printer
    ensure_slide_printer(console)
    from nbpress.wizard import run_wizard
    run_wizard()


@app.command(name="version")
def version_cmd():
    """Mostrar la versión de nbpress y el motor Typst."""
    typst_ver = getattr(typst, "__version__", "0.15.0")
    console.print(
        Panel(
            f"[bold cyan]nbpress[/bold cyan] versión [green]{__version__}[/green]\n"
            f"[bold cyan]Typst Engine[/bold cyan] versión [green]{typst_ver}[/green]",
            title="📖 Información de Versión",
            border_style="blue",
        )
    )


@app.command(name="info")
def info_cmd(
    notebook: Path = typer.Argument(
        ...,
        help="Ruta al archivo .ipynb a inspeccionar",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    )
):
    """Inspeccionar la estructura, celdas, metadatos y gráficos de un cuaderno Jupyter."""
    try:
        doc = load_notebook(notebook)
    except Exception as e:
        console.print(f"[bold red]Error al cargar el notebook:[/bold red] {e}")
        raise typer.Exit(1)

    table = Table(title=f"Notebook: [bold green]{notebook.name}[/bold green]", border_style="cyan")
    table.add_column("Propiedad", style="cyan", justify="right")
    table.add_column("Detalle", style="white")

    table.add_row("Título detectado", doc.title)
    if doc.authors:
        table.add_row("Autores", ", ".join(doc.authors))
    
    total_cells = len(doc.cells)
    md_cells = sum(1 for c in doc.cells if c.cell_type.value == "markdown")
    code_cells = sum(1 for c in doc.cells if c.cell_type.value == "code")
    raw_cells = sum(1 for c in doc.cells if c.cell_type.value == "raw")

    table.add_row("Total de celdas", str(total_cells))
    table.add_row("Celdas Markdown", f"{md_cells} ({md_cells/total_cells*100:.1f}%)" if total_cells else "0")
    table.add_row("Celdas de Código", f"{code_cells} ({code_cells/total_cells*100:.1f}%)" if total_cells else "0")
    if raw_cells:
        table.add_row("Celdas Raw", str(raw_cells))

    # Output statistics
    total_images = sum(
        sum(1 for out in c.outputs if out.has_image) for c in doc.cells
    )
    total_tables = sum(
        sum(1 for out in c.outputs if out.has_html_table) for c in doc.cells
    )
    total_errors = sum(
        sum(1 for out in c.outputs if out.output_type.value == "error") for c in doc.cells
    )

    table.add_row("Gráficos/Imágenes", f"[bold magenta]{total_images}[/bold magenta]")
    table.add_row("Tablas DataFrames", f"[bold yellow]{total_tables}[/bold yellow]")
    if total_errors > 0:
        table.add_row("Celdas con Error", f"[bold red]{total_errors}[/bold red]")

    # Slides statistics
    slides_count = sum(1 for c in doc.cells if c.is_slide_starter)
    table.add_row("Diapositivas / Secciones", f"[bold blue]{slides_count}[/bold blue]")

    console.print(table)


def parse_layouts(layout_str: str, all_flag: bool) -> List[LayoutMode]:
    """Parse comma-separated layouts or all-flag into a list of LayoutMode."""
    if all_flag or layout_str.strip().lower() in ("all", "todos", "*"):
        return [LayoutMode.DOCUMENT, LayoutMode.SLIDES, LayoutMode.HANDOUT, LayoutMode.CHEATSHEET]

    mode_map = {
        "document": LayoutMode.DOCUMENT,
        "doc": LayoutMode.DOCUMENT,
        "report": LayoutMode.DOCUMENT,
        "slides": LayoutMode.SLIDES,
        "slide": LayoutMode.SLIDES,
        "presentacion": LayoutMode.SLIDES,
        "handout": LayoutMode.HANDOUT,
        "handouts": LayoutMode.HANDOUT,
        "apuntes": LayoutMode.HANDOUT,
        "cheatsheet": LayoutMode.CHEATSHEET,
        "cheat": LayoutMode.CHEATSHEET,
        "resumen": LayoutMode.CHEATSHEET,
    }

    parts = [p.strip().lower() for p in layout_str.split(",") if p.strip()]
    resolved: List[LayoutMode] = []
    for p in parts:
        if p in ("all", "todos", "*"):
            return [LayoutMode.DOCUMENT, LayoutMode.SLIDES, LayoutMode.HANDOUT, LayoutMode.CHEATSHEET]
        if p in mode_map and mode_map[p] not in resolved:
            resolved.append(mode_map[p])

    return resolved or [LayoutMode.DOCUMENT]


@app.command(name="build")
def build_cmd(
    notebooks: List[Path] = typer.Argument(
        ...,
        help="Uno o varios archivos .ipynb a compilar",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Archivo PDF de salida o directorio de destino si son varios notebooks",
    ),
    layout: str = typer.Option(
        "document",
        "-l",
        "--layout",
        help="Maquetación o lista separada por comas ('document', 'slides', 'handout', 'cheatsheet', 'all')",
    ),
    all_layouts: bool = typer.Option(
        False,
        "--all-layouts",
        help="Compilar simultáneamente todas las arquitecturas (documento, slides, handout, cheatsheet)",
    ),
    theme: DocTheme = typer.Option(
        DocTheme.EDITORIAL,
        "-t",
        "--theme",
        help="Tema y arquitectura visual: 'editorial', 'mid-century', 'minimal'",
    ),
    paper: PaperSize = typer.Option(
        PaperSize.A4,
        "-p",
        "--paper",
        help="Tamaño de papel: 'a4', 'us-letter', 'a5'",
    ),
    handout_style: HandoutNoteStyle = typer.Option(
        HandoutNoteStyle.LINES,
        "--handout-style",
        help="Estilo de notas en handout: 'lines' (pauta), 'grid' (cuadrícula), 'dots' (bullet points), 'blank' (blanco)",
    ),
    handout_layout: HandoutDisposition = typer.Option(
        HandoutDisposition.ONE_UP,
        "--handout-layout",
        help="Disposición de diapositivas en handout: '1-up' (1 por pág.) o '2-up' (2 por pág.)",
    ),
    study_header: bool = typer.Option(
        False,
        "--study-header",
        help="Incluir cabecera de estudio y apuntes en handout",
    ),
    study_title: Optional[str] = typer.Option(
        None,
        "--study-title",
        help="Título o materia para la cabecera de estudio",
    ),
    eco: bool = typer.Option(
        False,
        "--eco",
        help="Modo ahorro de tinta y tóner (fondos blancos y alto contraste)",
    ),
    gutter: Optional[str] = typer.Option(
        None,
        "--gutter",
        help="Margen adicional de encuadernación en lomo (ej: '1.2cm')",
    ),
    cover: bool = typer.Option(
        True,
        "--cover/--no-cover",
        help="Incluir portada editorial en modo documento",
    ),
    toc: bool = typer.Option(
        True,
        "--toc/--no-toc",
        help="Generar tabla de contenidos en modo documento",
    ),
    show_code: bool = typer.Option(
        True,
        "--show-code/--no-code",
        help="Mostrar bloques de código fuente",
    ),
    line_numbers: bool = typer.Option(
        True,
        "--line-numbers/--no-line-numbers",
        help="Mostrar números de línea en celdas de código",
    ),
    max_output_lines: int = typer.Option(
        35,
        "--max-output-lines",
        help="Máximo de líneas en salidas de consola antes de truncar",
    ),
    handout_lines: int = typer.Option(
        8,
        "--handout-lines",
        help="Número de líneas pautadas para notas manuscritas en modo handout",
    ),
    keep_typ: bool = typer.Option(
        False,
        "--keep-typ",
        help="Guardar el archivo fuente de Typst (.typ) junto al PDF generado",
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        help="Sobrescribir el título del documento",
    ),
    author: Optional[str] = typer.Option(
        None,
        "--author",
        help="Sobrescribir el autor del documento",
    ),
):
    """
    Compilar cuadernos Jupyter (.ipynb) en PDFs limpios de alta calidad editorial.
    Soporta múltiples arquitecturas y maquetaciones simultáneas y diseño Mid-Century Modern.
    """
    chosen_layouts = parse_layouts(layout, all_layouts)

    config = NbpressConfig(
        layout=chosen_layouts[0],
        layouts=chosen_layouts,
        theme=theme,
        paper=paper,
        eco=eco,
        gutter=gutter,
        cover=cover,
        toc=toc,
        show_code=show_code,
        line_numbers=line_numbers,
        max_output_lines=max_output_lines,
        handout_note_lines=handout_lines,
        handout_note_style=handout_style,
        handout_disposition=handout_layout,
        handout_study_header=study_header,
        handout_study_title=study_title,
        title_override=title,
        author_override=author,
    )

    layouts_desc = ", ".join(l.value for l in chosen_layouts)
    console.print(
        f"[bold cyan]📖 nbpress[/bold cyan] iniciando compilación "
        f"([bold yellow]{layouts_desc}[/bold yellow], tema: [magenta]{theme.value}[/magenta], papel: {paper.value})"
    )

    results_table = Table(border_style="green", header_style="bold green")
    results_table.add_column("Cuaderno", style="cyan")
    results_table.add_column("Maquetación", style="yellow")
    results_table.add_column("PDF Generado", style="white")
    results_table.add_column("Tamaño", justify="right", style="magenta")
    results_table.add_column("Tiempo", justify="right", style="yellow")

    for nb_file in notebooks:
        if nb_file.is_dir():
            continue

        with console.status(f"[bold blue]Procesando {nb_file.name}...[/bold blue]"):
            try:
                if len(chosen_layouts) > 1:
                    out_dir = output if (output and output.is_dir()) else nb_file.parent
                    multi_res = generate_multiple_pdfs(
                        notebook_path=nb_file,
                        layouts=chosen_layouts,
                        output_dir=out_dir,
                        config=config,
                        keep_typ_source=keep_typ,
                    )
                    for l_mode, (pdf_path, duration) in multi_res.items():
                        file_size_kb = pdf_path.stat().st_size / 1024
                        results_table.add_row(
                            nb_file.name,
                            l_mode.value,
                            pdf_path.name,
                            f"{file_size_kb:.1f} KB",
                            f"{duration*1000:.0f} ms",
                        )
                else:
                    # Single layout target
                    if output and output.is_dir():
                        target_pdf = output / nb_file.with_suffix(".pdf").name
                    elif output and len(notebooks) == 1:
                        target_pdf = output
                    else:
                        target_pdf = nb_file.with_suffix(".pdf")

                    pdf_path, duration = generate_pdf(
                        notebook_path=nb_file,
                        output_pdf_path=target_pdf,
                        config=config,
                        keep_typ_source=keep_typ,
                    )
                    file_size_kb = pdf_path.stat().st_size / 1024
                    results_table.add_row(
                        nb_file.name,
                        chosen_layouts[0].value,
                        pdf_path.name,
                        f"{file_size_kb:.1f} KB",
                        f"{duration*1000:.0f} ms",
                    )
            except Exception as e:
                console.print(f"[bold red]❌ Error al compilar {nb_file.name}:[/bold red] {e}")
                raise typer.Exit(1)

    console.print(results_table)
    console.print("[bold green]✔ Compilación completada con éxito.[/bold green]")


@app.command(name="preview")
def preview_cmd(
    notebook: Path = typer.Argument(
        ...,
        help="Ruta al archivo .ipynb a previsualizar",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    layout: LayoutMode = typer.Option(
        LayoutMode.DOCUMENT,
        "-l",
        "--layout",
        help="Maquetación: 'document', 'slides', 'handout', 'cheatsheet'",
    ),
    theme: DocTheme = typer.Option(
        DocTheme.EDITORIAL,
        "-t",
        "--theme",
        help="Tema y diseño visual: 'editorial', 'mid-century', 'minimal'",
    ),
    paper: PaperSize = typer.Option(
        PaperSize.A4,
        "-p",
        "--paper",
        help="Tamaño de papel: 'a4', 'us-letter', 'a5'",
    ),
    eco: bool = typer.Option(
        False,
        "--eco",
        help="Modo ahorro de tinta y tóner",
    ),
):
    """
    Compilar el cuaderno y abrirlo inmediatamente en el visor de documentos predeterminado.
    """
    import os
    import subprocess

    config = NbpressConfig(layout=layout, theme=theme, paper=paper, eco=eco)
    target_pdf = notebook.with_suffix(".pdf")

    console.print(f"[bold cyan]📖 nbpress preview:[/bold cyan] Generando vista previa de [green]{notebook.name}[/green] ({theme.value})...")
    pdf_path, duration = generate_pdf(notebook, target_pdf, config=config)
    console.print(f"[bold green]✔ PDF generado en {duration*1000:.0f} ms.[/bold green] Abriendo visor...")

    try:
        if sys.platform == "win32":
            os.startfile(str(pdf_path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(pdf_path)], check=False)
        else:
            subprocess.run(["xdg-open", str(pdf_path)], check=False)
    except Exception as e:
        console.print(f"[yellow]No se pudo abrir automáticamente el visor:[/yellow] {e}")


if __name__ == "__main__":
    app()
