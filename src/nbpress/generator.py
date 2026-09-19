"""
Generator and orchestrator: converts NotebookDocument into Typst source and compiles to PDF.
"""

from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import jinja2
import typst

from nbpress.config import LayoutMode, NbpressConfig
from nbpress.models import CellType, NotebookCell, NotebookDocument, SlideType
from nbpress.parser import load_notebook
from nbpress.processors.code import format_code_cell
from nbpress.processors.markdown import markdown_to_typst
from nbpress.processors.outputs import format_outputs


TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_template_env() -> jinja2.Environment:
    """Initialize Jinja2 environment with the templates directory."""
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def group_cells_into_slides(cells: List[NotebookCell]) -> List[Dict[str, Any]]:
    """
    Group notebook cells into slides based on slideshow metadata or H1/H2 headers.
    """
    slides: List[Dict[str, Any]] = []
    current_title = "Introducción"
    current_content: List[str] = []

    for cell in cells:
        # Check if cell initiates a new slide
        if cell.is_slide_starter and current_content:
            slides.append({
                "title": current_title,
                "content": "\n#v(6pt)\n".join(current_content),
            })
            current_content = []
            if cell.heading_text:
                current_title = cell.heading_text
            else:
                current_title = f"Diapositiva {len(slides) + 1}"
        elif cell.heading_text and not current_content:
            current_title = cell.heading_text

        # Append cell representation
        # Note: Handout slide content will be rendered items
        pass

    return slides


def render_cells_to_typst(
    cells: List[NotebookCell],
    assets_dir: Path,
    config: NbpressConfig,
) -> List[str]:
    """
    Render all notebook cells into a sequence of Typst code blocks.
    """
    rendered_items: List[str] = []

    for cell in cells:
        if cell.cell_type == CellType.MARKDOWN:
            typ_md = markdown_to_typst(cell.source)
            if typ_md.strip():
                rendered_items.append(typ_md)

        elif cell.cell_type == CellType.CODE:
            code_parts = []
            # Render Code block if enabled
            if config.show_code:
                code_typ = format_code_cell(cell, config=config)
                if code_typ:
                    code_parts.append(code_typ)

            # Render Outputs
            if cell.outputs:
                out_typ_list = format_outputs(
                    outputs=cell.outputs,
                    assets_dir=assets_dir,
                    config=config,
                    cell_idx=cell.index,
                )
                code_parts.extend(out_typ_list)

            if code_parts:
                rendered_items.append("\n#v(4pt)\n".join(code_parts))

    return rendered_items


def build_slides_list(
    notebook: NotebookDocument,
    assets_dir: Path,
    config: NbpressConfig,
) -> List[Dict[str, Any]]:
    """Build list of slides from notebook cells."""
    slides: List[Dict[str, Any]] = []
    current_title = notebook.title
    current_items: List[str] = []

    def _sanitize(t: str) -> str:
        return t.replace("[", r"\[").replace("]", r"\]")

    for cell in notebook.cells:
        is_new = cell.is_slide_starter
        if is_new and current_items:
            slides.append({
                "title": _sanitize(current_title),
                "content": "\n#v(6pt)\n".join(current_items),
            })
            current_items = []
            current_title = cell.heading_text or f"Tema {len(slides) + 1}"
        elif cell.heading_text and not current_items:
            current_title = cell.heading_text

        # Render this single cell
        rendered = render_cells_to_typst([cell], assets_dir=assets_dir, config=config)
        if rendered:
            current_items.extend(rendered)

    if current_items:
        slides.append({
            "title": _sanitize(current_title),
            "content": "\n#v(6pt)\n".join(current_items),
        })

    if not slides:
        slides.append({
            "title": _sanitize(notebook.title),
            "content": "El cuaderno no contiene celdas ejecutables.",
        })

    return slides


def ensure_images_exist(typ_content: str, build_dir: Path) -> str:
    """Ensure all images referenced in Typst exist on disk or create a placeholder."""
    import re
    from PIL import Image, ImageDraw

    # Normalize relative ./ prefixes in typ_content
    typ_content = typ_content.replace('"./', '"')

    # Replace .gif references with .png since Typst doesn't support GIF
    typ_content = typ_content.replace('.gif"', '.png"').replace(".gif'", ".png'")

    img_matches = re.findall(r'#nb-image\("([^"]+)"', typ_content)
    for rel_path in img_matches:
        clean_rel = rel_path.lstrip("/").replace("\\", "/")
        target_path = build_dir / clean_rel
        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            # Create a clean fallback image with PIL
            img = Image.new("RGB", (600, 180), color=(245, 247, 250))
            draw = ImageDraw.Draw(img)
            draw.rectangle([(1, 1), (598, 178)], outline=(206, 212, 218), width=2)
            draw.text((25, 80), f"Imagen no encontrada: {clean_rel}", fill=(108, 117, 125))
            try:
                img.save(target_path)
            except Exception:
                pass

    return typ_content


def generate_typst_source(
    notebook: NotebookDocument,
    config: NbpressConfig,
    assets_dir: Path,
) -> str:
    """
    Generate the complete .typ file content for a given notebook and config.
    """
    env = get_template_env()

    # Calculate inside margin with optional gutter
    margin_inside = config.margin_inside
    if config.gutter:
        margin_inside = f"{config.margin_inside} + {config.gutter}"

    base_context = {
        "title": notebook.title,
        "subtitle": notebook.subtitle,
        "authors": notebook.authors,
        "date": notebook.date,
        "abstract": notebook.abstract,
        "language": notebook.language,
        "paper": config.paper.value,
        "margin_top": config.margin_top,
        "margin_bottom": config.margin_bottom,
        "margin_inside": margin_inside,
        "margin_outside": config.margin_outside,
        "cover": config.cover,
        "toc": config.toc,
        "page_numbers": config.page_numbers,
        "eco": config.eco,
    }

    if config.layout == LayoutMode.SLIDES:
        template = env.get_template("slides.typ")
        slides = build_slides_list(notebook, assets_dir=assets_dir, config=config)
        context = {
            **base_context,
            "slides": slides,
        }
        return template.render(**context)

    elif config.layout == LayoutMode.HANDOUT:
        template = env.get_template("handout.typ")
        slides = build_slides_list(notebook, assets_dir=assets_dir, config=config)
        context = {
            **base_context,
            "slides": slides,
            "note_lines": config.handout_note_lines,
            "grid_style": config.handout_grid_style,
        }
        return template.render(**context)

    elif config.layout == LayoutMode.CHEATSHEET:
        template = env.get_template("cheatsheet.typ")
        rendered_items = render_cells_to_typst(notebook.cells, assets_dir=assets_dir, config=config)
        context = {
            **base_context,
            "rendered_items": rendered_items,
        }
        return template.render(**context)

    else:  # LayoutMode.DOCUMENT
        template = env.get_template("document.typ")
        rendered_items = render_cells_to_typst(notebook.cells, assets_dir=assets_dir, config=config)
        context = {
            **base_context,
            "rendered_items": rendered_items,
        }
        return template.render(**context)


def generate_pdf(
    notebook_path: Path | str,
    output_pdf_path: Optional[Path | str] = None,
    config: Optional[NbpressConfig] = None,
    keep_typ_source: bool = False,
) -> Tuple[Path, float]:
    """
    Convert a Jupyter notebook to PDF.
    
    Returns:
        Tuple[Path, float]: (Path to generated PDF, compilation time in seconds)
    """
    if config is None:
        config = NbpressConfig()

    nb_path = Path(notebook_path)
    if not nb_path.exists():
        raise FileNotFoundError(f"Notebook file not found: {nb_path}")

    # Determine output PDF path
    if output_pdf_path:
        out_pdf = Path(output_pdf_path)
    else:
        out_pdf = nb_path.with_suffix(".pdf")
    
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.perf_counter()

    # Load and normalize notebook
    doc = load_notebook(
        nb_path,
        title_override=config.title_override,
        author_override=config.author_override,
    )

    # Use a build directory for Typst and assets
    with tempfile.TemporaryDirectory(prefix="nbpress_build_") as tmp_dir:
        build_dir = Path(tmp_dir)
        assets_dir = build_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Copy external asset folders from notebook directory if present
        for asset_folder_name in ("imgs", "images", "img", "figures"):
            src_folder = nb_path.parent / asset_folder_name
            if src_folder.is_dir():
                target_folder = build_dir / asset_folder_name
                shutil.copytree(src_folder, target_folder, dirs_exist_ok=True)
                
                # Sanitize images for Typst compatibility (convert GIF to PNG, fix extension/signature mismatches)
                from PIL import Image
                for img_file in target_folder.glob("*.*"):
                    try:
                        ext = img_file.suffix.lower().lstrip(".")
                        if ext == "gif":
                            png_target = img_file.with_suffix(".png")
                            with Image.open(img_file) as im:
                                im.convert("RGB").save(png_target, "PNG")
                        elif ext in ("png", "jpg", "jpeg", "webp"):
                            with Image.open(img_file) as im:
                                real_fmt = im.format
                                if ext == "png" and real_fmt != "PNG":
                                    im.convert("RGB").save(img_file, "PNG")
                                elif ext in ("jpg", "jpeg") and real_fmt not in ("JPEG", "MPO"):
                                    im.convert("RGB").save(img_file, "JPEG")
                    except Exception:
                        pass

        # Copy base.typ macro definitions to build directory
        base_src = TEMPLATES_DIR / "base.typ"
        shutil.copy(base_src, build_dir / "base.typ")

        # Generate main .typ content
        typ_content = generate_typst_source(doc, config, assets_dir=assets_dir)
        
        # Ensure all referenced images exist or have a placeholder
        typ_content = ensure_images_exist(typ_content, build_dir)

        main_typ_path = build_dir / "main.typ"
        main_typ_path.write_text(typ_content, encoding="utf-8")

        # If user requested to keep Typst source
        if keep_typ_source:
            debug_typ_path = out_pdf.with_suffix(".typ")
            debug_typ_path.write_text(typ_content, encoding="utf-8")
            # also copy base.typ and assets alongside
            shutil.copy(base_src, out_pdf.parent / "base.typ")
            target_assets = out_pdf.parent / "assets"
            if assets_dir.exists():
                shutil.copytree(assets_dir, target_assets, dirs_exist_ok=True)

        # Compile with Typst
        typst.compile(
            input=main_typ_path,
            output=out_pdf,
            root=build_dir,
        )

    compile_duration = time.perf_counter() - start_time
    return out_pdf, compile_duration
