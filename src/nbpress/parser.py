"""
Notebook parser and normalizer for nbpress.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import nbformat

from nbpress.models import (
    CellOutput,
    CellType,
    NotebookCell,
    NotebookDocument,
    OutputType,
    SlideType,
)


def extract_heading_info(source: str) -> Tuple[Optional[int], Optional[str]]:
    """Extract heading level and text from the first line of markdown if it starts with #."""
    for line in source.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            # Clean up trailing hashes or markdown links
            text = re.sub(r"\s+#+$", "", text)
            return level, text
        break
    return None, None


def parse_slide_type(cell_metadata: Dict[str, Any]) -> SlideType:
    """Parse RISE / Reveal.js slideshow metadata from cell."""
    slideshow = cell_metadata.get("slideshow", {})
    raw_type = slideshow.get("slide_type", "").lower()
    
    mapping = {
        "slide": SlideType.SLIDE,
        "subslide": SlideType.SUBSLIDE,
        "fragment": SlideType.FRAGMENT,
        "skip": SlideType.SKIP,
        "notes": SlideType.NOTES,
    }
    return mapping.get(raw_type, SlideType.NONE)


def parse_output(raw_output: Dict[str, Any]) -> CellOutput:
    """Parse a single raw nbformat cell output."""
    raw_type = raw_output.get("output_type", "")
    
    type_mapping = {
        "execute_result": OutputType.EXECUTE_RESULT,
        "display_data": OutputType.DISPLAY_DATA,
        "stream": OutputType.STREAM,
        "error": OutputType.ERROR,
    }
    output_type = type_mapping.get(raw_type, OutputType.DISPLAY_DATA)

    text = None
    if "text" in raw_output:
        raw_text = raw_output["text"]
        text = "".join(raw_text) if isinstance(raw_text, list) else str(raw_text)
    
    data = {}
    if "data" in raw_output and isinstance(raw_output["data"], dict):
        for mime, content in raw_output["data"].items():
            if isinstance(content, list):
                data[mime] = "".join(content)
            else:
                data[mime] = content

    return CellOutput(
        output_type=output_type,
        text=text,
        data=data,
        name=raw_output.get("name"),
        ename=raw_output.get("ename"),
        evalue=raw_output.get("evalue"),
        traceback=raw_output.get("traceback"),
    )


def load_notebook(
    filepath: Path | str,
    title_override: Optional[str] = None,
    author_override: Optional[str] = None,
) -> NotebookDocument:
    """
    Read and normalize a Jupyter notebook (.ipynb) into a NotebookDocument.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Notebook not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    cells: List[NotebookCell] = []
    inferred_title = None
    inferred_authors: List[str] = []
    inferred_subtitle = None

    # Check notebook metadata
    nb_meta = nb.get("metadata", {})
    if "title" in nb_meta:
        inferred_title = nb_meta["title"]
    if "authors" in nb_meta:
        raw_authors = nb_meta["authors"]
        if isinstance(raw_authors, list):
            inferred_authors = [
                a.get("name", str(a)) if isinstance(a, dict) else str(a)
                for a in raw_authors
            ]

    # Process cells
    for idx, raw_cell in enumerate(nb.get("cells", [])):
        raw_type = raw_cell.get("cell_type", "")
        cell_type = CellType.RAW
        if raw_type == "markdown":
            cell_type = CellType.MARKDOWN
        elif raw_type == "code":
            cell_type = CellType.CODE

        raw_source = raw_cell.get("source", "")
        source = "".join(raw_source) if isinstance(raw_source, list) else str(raw_source)
        
        cell_meta = raw_cell.get("metadata", {})
        slide_type = parse_slide_type(cell_meta)
        
        heading_level, heading_text = (None, None)
        if cell_type == CellType.MARKDOWN:
            heading_level, heading_text = extract_heading_info(source)
            # Infer title from first H1 if not yet discovered
            if inferred_title is None and heading_level == 1 and heading_text:
                inferred_title = heading_text

        outputs = [parse_output(out) for out in raw_cell.get("outputs", [])]
        exec_count = raw_cell.get("execution_count")

        cells.append(
            NotebookCell(
                index=idx,
                cell_type=cell_type,
                source=source,
                execution_count=exec_count,
                outputs=outputs,
                metadata=cell_meta,
                slide_type=slide_type,
                heading_level=heading_level,
                heading_text=heading_text,
            )
        )

    # Defaults
    if title_override:
        final_title = title_override
    elif inferred_title:
        final_title = inferred_title
    else:
        # Fallback to file stem nicely formatted
        final_title = path.stem.replace("_", " ").replace("-", " ").title()

    final_authors = [author_override] if author_override else inferred_authors

    return NotebookDocument(
        title=final_title,
        subtitle=inferred_subtitle,
        authors=final_authors,
        cells=cells,
        metadata=nb_meta,
    )
