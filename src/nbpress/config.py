"""
Configuration models and presets for nbpress.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LayoutMode(str, Enum):
    DOCUMENT = "document"
    HANDOUT = "handout"
    CHEATSHEET = "cheatsheet"
    SLIDES = "slides"


class PaperSize(str, Enum):
    A4 = "a4"
    LETTER = "us-letter"
    A5 = "a5"
    PRESENTATION_16_9 = "presentation-16-9"
    PRESENTATION_4_3 = "presentation-4-3"


class DocTheme(str, Enum):
    EDITORIAL = "editorial"
    MID_CENTURY = "mid-century"
    MINIMAL = "minimal"


class HandoutNoteStyle(str, Enum):
    LINES = "lines"
    GRID = "grid"
    DOTS = "dots"
    BLANK = "blank"


class HandoutDisposition(str, Enum):
    ONE_UP = "1-up"
    TWO_UP = "2-up"


class NbpressConfig(BaseModel):
    # Layout and Paper
    layout: LayoutMode = Field(default=LayoutMode.DOCUMENT, description="Maquetación del documento")
    layouts: list[LayoutMode] = Field(default_factory=list, description="Lista de maquetaciones para compilación múltiple")
    paper: PaperSize = Field(default=PaperSize.A4, description="Tamaño de papel para impresión")
    theme: DocTheme = Field(default=DocTheme.EDITORIAL, description="Tema o estilo de diseño (editorial, mid-century, minimal)")
    
    # Print and Style Optimizations
    eco: bool = Field(default=False, description="Modo eco / ahorro de tinta (fondos claros, alto contraste)")
    gutter: Optional[str] = Field(default=None, description="Margen adicional de encuadernación (ej: '1.5cm')")
    margin_top: str = Field(default="2.2cm", description="Margen superior")
    margin_bottom: str = Field(default="2.2cm", description="Margen inferior")
    margin_inside: str = Field(default="2.2cm", description="Margen interior (lomo)")
    margin_outside: str = Field(default="2.0cm", description="Margen exterior")

    # Document Elements
    cover: bool = Field(default=True, description="Incluir portada en modo documento")
    toc: bool = Field(default=True, description="Incluir índice de contenidos en modo documento")
    page_numbers: bool = Field(default=True, description="Mostrar numeración 'Pág. X de Y'")
    header_title: bool = Field(default=True, description="Mostrar título en encabezado de páginas")

    # Code and Outputs
    show_code: bool = Field(default=True, description="Mostrar celdas de código")
    show_prompts: bool = Field(default=True, description="Mostrar etiquetas In [x] / Out [x]")
    line_numbers: bool = Field(default=True, description="Mostrar números de línea en celdas de código")
    max_output_lines: int = Field(default=35, description="Límite máximo de líneas para salidas de texto de consola")
    
    # Handout & Slide-Printer Specifics
    handout_note_lines: int = Field(default=8, description="Número de líneas para notas manuscritas por diapositiva")
    handout_note_style: HandoutNoteStyle = Field(default=HandoutNoteStyle.LINES, description="Estilo de notas: 'lines', 'grid', 'dots', 'blank'")
    handout_grid_style: str = Field(default="lines", description="Retrocompatibilidad con handout_note_style")
    handout_disposition: HandoutDisposition = Field(default=HandoutDisposition.ONE_UP, description="Disposición en handout: 1-up o 2-up")
    handout_study_header: bool = Field(default=False, description="Incluir cabecera de estudio en handout")
    handout_study_title: Optional[str] = Field(default=None, description="Título para la cabecera de estudio")
    handout_duplex: bool = Field(default=False, description="Soporte duplex para alternar márgenes de encuadernación")
    use_slide_printer_api: bool = Field(default=True, description="Usar el motor oficial de slide-printer para procesar handouts")

    # Metadata Overrides
    title_override: Optional[str] = Field(default=None, description="Sobrescribir título del documento")
    author_override: Optional[str] = Field(default=None, description="Sobrescribir autor(es)")
