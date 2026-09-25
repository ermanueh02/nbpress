"""
Generator and orchestrator: converts NotebookDocument into Typst source and compiles to PDF.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import jinja2
import typst

from nbpress.config import LayoutMode, NbpressConfig
from nbpress.models import CellType, NotebookCell, NotebookDocument, OutputType, SlideType
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


def estimate_cell_height_pts(cell: NotebookCell, config: NbpressConfig) -> float:
    """
    Estimate vertical height in points of a rendered cell on a 16:9 slide.
    Available printable height on a 16:9 presentation slide is ~270-300 pt.
    """
    height = 0.0
    if cell.cell_type == CellType.MARKDOWN:
        lines = cell.source.splitlines()
        if cell.heading_level:
            height += 25.0
        has_md_img = bool(re.search(r"<img|!\[", cell.source, re.IGNORECASE))
        if has_md_img:
            height += 220.0
        text_lines = [l for l in lines if l.strip() and not l.strip().startswith("#") and not re.search(r"<img|!\[", l)]
        height += len(text_lines) * 14.0
        if "$$" in cell.source or r"\[" in cell.source:
            height += 30.0

    elif cell.cell_type == CellType.CODE:
        if config.show_code:
            code_lines = [l for l in cell.source.splitlines() if l.strip()]
            height += 20.0 + min(len(code_lines), 15) * 11.0

        for out in cell.outputs:
            if out.has_image:
                height += 220.0
            elif out.has_html_table:
                html = out.data.get("text/html", "")
                if isinstance(html, list):
                    html = "".join(html)
                rows_count = html.count("<tr")
                height += 25.0 + min(rows_count, 10) * 14.0
            elif out.output_type in (OutputType.STREAM, OutputType.EXECUTE_RESULT):
                text = out.text or out.data.get("text/plain", "")
                if isinstance(text, list):
                    text = "".join(text)
                if text and not re.match(r"^<matplotlib\..*>$|^<Axes.*>$|^\[<matplotlib\..*>\]$", text.strip()):
                    tlines = text.strip().splitlines()
                    height += 15.0 + min(len(tlines), 8) * 10.0

    return max(height, 10.0)


def build_slides_list(
    notebook: NotebookDocument,
    assets_dir: Path,
    config: NbpressConfig,
) -> List[Dict[str, Any]]:
    """Build list of slides from notebook cells with vertical budgeting and overflow prevention."""
    MAX_SLIDE_HEIGHT = 270.0  # Points available for content on a 16:9 slide
    slides: List[Dict[str, Any]] = []
    current_title = notebook.title
    current_items: List[str] = []
    current_height = 0.0

    def _sanitize(t: str) -> str:
        return t.replace("[", r"\[").replace("]", r"\]")

    for cell in notebook.cells:
        # Ignore completely empty cells
        if not cell.source.strip() and not cell.outputs:
            continue

        is_new = cell.is_slide_starter
        cell_h = estimate_cell_height_pts(cell, config)

        need_break = False
        if is_new and current_items:
            need_break = True
        elif current_items and (current_height + cell_h > MAX_SLIDE_HEIGHT):
            need_break = True

        if need_break:
            slides.append({
                "title": _sanitize(current_title),
                "content": "\n#v(6pt)\n".join(current_items),
            })
            current_items = []
            current_height = 0.0
            if cell.heading_text:
                current_title = cell.heading_text
            else:
                current_title = f"{current_title} (cont.)" if not current_title.endswith("(cont.)") else current_title
        elif cell.heading_text and not current_items:
            current_title = cell.heading_text

        # Render cell
        if cell.cell_type == CellType.MARKDOWN:
            strip_hdr = bool(cell.heading_text and cell.heading_level)
            typ_md = markdown_to_typst(cell.source, strip_first_heading=strip_hdr)
            if typ_md.strip():
                current_items.append(typ_md.strip())
                current_height += cell_h

        elif cell.cell_type == CellType.CODE:
            code_typ = format_code_cell(cell, config=config) if config.show_code else None
            out_typ_list = format_outputs(cell.outputs, assets_dir=assets_dir, config=config, cell_idx=cell.index) if cell.outputs else []

            img_outs = [o for o in out_typ_list if "#nb-image(" in o]
            non_img_outs = [o for o in out_typ_list if "#nb-image(" not in o]

            code_lines_count = len([l for l in cell.source.splitlines() if l.strip()])
            code_h = 20.0 + min(code_lines_count, 15) * 11.0 if code_typ else 0.0
            img_h = 220.0 if img_outs else 0.0

            # If code + image output together exceed MAX_SLIDE_HEIGHT, separate them into 2 slides!
            if code_typ and img_outs and (code_h + img_h > MAX_SLIDE_HEIGHT or code_lines_count > 4):
                if current_items and (current_height + code_h > MAX_SLIDE_HEIGHT):
                    slides.append({
                        "title": _sanitize(current_title),
                        "content": "\n#v(6pt)\n".join(current_items),
                    })
                    current_items = []
                    current_height = 0.0
                    current_title = f"{current_title} (cont.)" if not current_title.endswith("(cont.)") else current_title

                parts = [code_typ]
                if non_img_outs:
                    parts.extend(non_img_outs)
                current_items.append("\n#v(4pt)\n".join(parts))

                slides.append({
                    "title": _sanitize(current_title),
                    "content": "\n#v(6pt)\n".join(current_items),
                })
                current_items = []
                current_height = 0.0

                current_title = f"{current_title} (cont.)" if not current_title.endswith("(cont.)") else current_title
                if len(img_outs) == 2:
                    current_items.append(f"#grid(columns: (1fr, 1fr), gutter: 12pt, [{img_outs[0]}], [{img_outs[1]}])")
                else:
                    current_items.extend(img_outs)
                current_height = img_h
            else:
                code_parts = []
                if code_typ:
                    code_parts.append(code_typ)
                if non_img_outs:
                    code_parts.extend(non_img_outs)
                if len(img_outs) == 2:
                    code_parts.append(f"#grid(columns: (1fr, 1fr), gutter: 12pt, [{img_outs[0]}], [{img_outs[1]}])")
                else:
                    code_parts.extend(img_outs)
                if code_parts:
                    current_items.append("\n#v(4pt)\n".join(code_parts))
                    current_height += cell_h

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

    theme_val = config.theme.value if hasattr(config.theme, "value") else str(config.theme)
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
        "theme": theme_val,
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
        note_style = config.handout_note_style.value if hasattr(config.handout_note_style, "value") else str(config.handout_note_style)
        if config.handout_grid_style and config.handout_grid_style != "lines":
            note_style = config.handout_grid_style
        context = {
            **base_context,
            "slides": slides,
            "note_lines": config.handout_note_lines,
            "grid_style": note_style,
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
                
                # Sanitize images for Typst compatibility
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

        # Check if Slide-Printer API should be used for Handout layout
        slide_printer_used = False
        if config.layout == LayoutMode.HANDOUT and config.use_slide_printer_api:
            try:
                from slide_printer import SlidePrinter, resolve_style

                # 1. Compile 16:9 widescreen presentation slides with Typst
                slides_cfg = config.model_copy(update={"layout": LayoutMode.SLIDES, "paper": config.paper})
                slides_typ = generate_typst_source(doc, slides_cfg, assets_dir=assets_dir)
                slides_typ = ensure_images_exist(slides_typ, build_dir)
                slides_typ_path = build_dir / "slides.typ"
                slides_typ_path.write_text(slides_typ, encoding="utf-8")

                temp_slides_pdf = build_dir / "slides.pdf"
                typst.compile(
                    input=slides_typ_path,
                    output=temp_slides_pdf,
                    root=build_dir,
                )

                # 2. Configure SlidePrinter
                gutter_pts = 0.0
                if config.gutter:
                    raw_g = config.gutter.lower().strip()
                    if raw_g.endswith("cm"):
                        gutter_pts = float(raw_g[:-2]) * 28.3465
                    elif raw_g.endswith("mm"):
                        gutter_pts = float(raw_g[:-2]) * 2.83465
                    elif raw_g.endswith("in"):
                        gutter_pts = float(raw_g[:-2]) * 72.0
                    elif raw_g.endswith("pt"):
                        gutter_pts = float(raw_g[:-2])

                paper_str = config.paper.value
                if "presentation" in paper_str:
                    paper_str = "a4"
                elif paper_str == "us-letter":
                    paper_str = "letter"

                note_style_str = config.handout_note_style.value if hasattr(config.handout_note_style, "value") else str(config.handout_note_style)
                if config.handout_grid_style and config.handout_grid_style != "lines":
                    note_style_str = config.handout_grid_style
                style_key = resolve_style(note_style_str)

                layout_str = config.handout_disposition.value if hasattr(config.handout_disposition, "value") else str(config.handout_disposition)

                sp_out_dir = build_dir / "sp_out"
                sp_out_dir.mkdir(parents=True, exist_ok=True)

                printer = SlidePrinter(
                    paper_size=paper_str,
                    margin=36.0,
                    step=14.0,
                    separation=10.0,
                    output_dir=str(sp_out_dir),
                    page_numbers=config.page_numbers,
                    study_header=config.handout_study_header,
                    study_title=config.handout_study_title or doc.title,
                    gutter_margin=gutter_pts,
                    duplex=config.handout_duplex,
                    layout=layout_str,
                    grayscale=config.eco,
                )

                processed = printer.process_file(
                    input_path=str(temp_slides_pdf),
                    styles=[style_key],
                    output_dir=str(sp_out_dir),
                )

                if processed and Path(processed[0]).exists():
                    shutil.copy2(processed[0], out_pdf)
                    slide_printer_used = True

                    if keep_typ_source:
                        debug_typ_path = out_pdf.with_suffix(".typ")
                        debug_typ_path.write_text(slides_typ, encoding="utf-8")
            except Exception:
                slide_printer_used = False

        if not slide_printer_used:
            # Native Typst compilation
            typ_content = generate_typst_source(doc, config, assets_dir=assets_dir)
            typ_content = ensure_images_exist(typ_content, build_dir)

            main_typ_path = build_dir / "main.typ"
            main_typ_path.write_text(typ_content, encoding="utf-8")

            if keep_typ_source:
                debug_typ_path = out_pdf.with_suffix(".typ")
                debug_typ_path.write_text(typ_content, encoding="utf-8")
                shutil.copy(base_src, out_pdf.parent / "base.typ")
                target_assets = out_pdf.parent / "assets"
                if assets_dir.exists():
                    shutil.copytree(assets_dir, target_assets, dirs_exist_ok=True)

            typst.compile(
                input=main_typ_path,
                output=out_pdf,
                root=build_dir,
            )

    compile_duration = time.perf_counter() - start_time
    return out_pdf, compile_duration


def generate_multiple_pdfs(
    notebook_path: Path | str,
    layouts: List[LayoutMode],
    output_dir: Optional[Path | str] = None,
    config: Optional[NbpressConfig] = None,
    keep_typ_source: bool = False,
) -> Dict[LayoutMode, Tuple[Path, float]]:
    """
    Generate multiple PDF layouts for a single notebook document.
    
    Returns:
        Dict[LayoutMode, Tuple[Path, float]]: Mapping of LayoutMode to (Path to PDF, duration in seconds)
    """
    if config is None:
        config = NbpressConfig()

    nb_path = Path(notebook_path)
    base_dir = Path(output_dir) if output_dir else nb_path.parent
    base_stem = nb_path.stem

    results: Dict[LayoutMode, Tuple[Path, float]] = {}

    suffix_map = {
        LayoutMode.DOCUMENT: "_doc.pdf" if len(layouts) > 1 else ".pdf",
        LayoutMode.SLIDES: "_slides.pdf",
        LayoutMode.HANDOUT: "_handout.pdf",
        LayoutMode.CHEATSHEET: "_cheatsheet.pdf",
    }

    for layout_mode in layouts:
        out_name = f"{base_stem}{suffix_map.get(layout_mode, f'_{layout_mode.value}.pdf')}"
        target_pdf = base_dir / out_name
        layout_cfg = config.model_copy(update={"layout": layout_mode})
        pdf_path, dur = generate_pdf(
            notebook_path=nb_path,
            output_pdf_path=target_pdf,
            config=layout_cfg,
            keep_typ_source=keep_typ_source,
        )
        results[layout_mode] = (pdf_path, dur)

    return results
