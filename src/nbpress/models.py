"""
Data models for notebooks, cells, and outputs in nbpress.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CellType(str, Enum):
    MARKDOWN = "markdown"
    CODE = "code"
    RAW = "raw"


class SlideType(str, Enum):
    NONE = "none"
    SLIDE = "slide"
    SUBSLIDE = "subslide"
    FRAGMENT = "fragment"
    SKIP = "skip"
    NOTES = "notes"


class OutputType(str, Enum):
    EXECUTE_RESULT = "execute_result"
    DISPLAY_DATA = "display_data"
    STREAM = "stream"
    ERROR = "error"


class CellOutput(BaseModel):
    output_type: OutputType
    text: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    name: Optional[str] = None  # e.g., 'stdout', 'stderr' for streams
    ename: Optional[str] = None
    evalue: Optional[str] = None
    traceback: Optional[List[str]] = None

    @property
    def has_image(self) -> bool:
        return any(
            mime in self.data
            for mime in ("image/png", "image/jpeg", "image/svg+xml", "image/webp")
        )

    @property
    def has_html_table(self) -> bool:
        if "text/html" in self.data:
            html = self.data["text/html"]
            if isinstance(html, list):
                html = "".join(html)
            return "<table" in html.lower()
        return False

    @property
    def image_mime_and_data(self) -> Optional[tuple[str, str]]:
        for mime in ("image/svg+xml", "image/png", "image/jpeg", "image/webp"):
            if mime in self.data:
                content = self.data[mime]
                if isinstance(content, list):
                    content = "".join(content)
                return mime, content
        return None


class NotebookCell(BaseModel):
    index: int
    cell_type: CellType
    source: str
    execution_count: Optional[int] = None
    outputs: List[CellOutput] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    slide_type: SlideType = SlideType.NONE
    heading_level: Optional[int] = None
    heading_text: Optional[str] = None

    @property
    def is_slide_starter(self) -> bool:
        """True if cell marks the beginning of a new slide or major section."""
        if self.slide_type in (SlideType.SLIDE, SlideType.SUBSLIDE):
            return True
        if self.cell_type == CellType.MARKDOWN and self.heading_level in (1, 2, 3):
            return True
        return False


class NotebookDocument(BaseModel):
    title: str
    subtitle: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    abstract: Optional[str] = None
    language: str = "es"
    cells: List[NotebookCell] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
