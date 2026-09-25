"""
Unit and end-to-end tests for multi-architecture document generation,
Mid-Century Modern theme, and Slide-Printer API integration.
"""

from pathlib import Path
import pytest
from typer.testing import CliRunner

from nbpress.cli import app, parse_layouts
from nbpress.config import (
    DocTheme,
    HandoutDisposition,
    HandoutNoteStyle,
    LayoutMode,
    NbpressConfig,
    PaperSize,
)
from nbpress.generator import generate_multiple_pdfs, generate_pdf

runner = CliRunner()
SAMPLES_DIR = Path(__file__).parent / "sample_notebooks"


def test_parse_layouts_utility():
    """Verify parsing comma-separated layouts and aliases."""
    res1 = parse_layouts("document,slides", all_flag=False)
    assert res1 == [LayoutMode.DOCUMENT, LayoutMode.SLIDES]

    res2 = parse_layouts("doc,handout,cheat", all_flag=False)
    assert res2 == [LayoutMode.DOCUMENT, LayoutMode.HANDOUT, LayoutMode.CHEATSHEET]

    res_all = parse_layouts("all", all_flag=False)
    assert len(res_all) == 4
    assert LayoutMode.DOCUMENT in res_all
    assert LayoutMode.SLIDES in res_all
    assert LayoutMode.HANDOUT in res_all
    assert LayoutMode.CHEATSHEET in res_all

    res_flag = parse_layouts("document", all_flag=True)
    assert len(res_flag) == 4


def test_generate_multiple_layouts_api(tmp_path: Path):
    """Test compiling multiple layouts simultaneously for a single notebook."""
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    layouts = [LayoutMode.DOCUMENT, LayoutMode.SLIDES, LayoutMode.CHEATSHEET]

    config = NbpressConfig(
        theme=DocTheme.MID_CENTURY,
        paper=PaperSize.A4,
    )

    results = generate_multiple_pdfs(
        notebook_path=nb_path,
        layouts=layouts,
        output_dir=tmp_path,
        config=config,
    )

    assert len(results) == 3
    for layout_mode in layouts:
        assert layout_mode in results
        pdf_path, duration = results[layout_mode]
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 1000
        assert duration > 0

    # Check file suffixes
    doc_pdf = tmp_path / "complete_features_doc.pdf"
    slides_pdf = tmp_path / "complete_features_slides.pdf"
    cheatsheet_pdf = tmp_path / "complete_features_cheatsheet.pdf"
    assert doc_pdf.exists()
    assert slides_pdf.exists()
    assert cheatsheet_pdf.exists()


def test_generate_handout_with_slide_printer_grid(tmp_path: Path):
    """Test handout generation with SlidePrinter API and grid (cuadrícula) style."""
    nb_path = SAMPLES_DIR / "slides_example.ipynb"
    out_pdf = tmp_path / "handout_grid.pdf"

    config = NbpressConfig(
        layout=LayoutMode.HANDOUT,
        handout_note_style=HandoutNoteStyle.GRID,
        handout_disposition=HandoutDisposition.ONE_UP,
        theme=DocTheme.MID_CENTURY,
        paper=PaperSize.A4,
        use_slide_printer_api=True,
    )

    pdf_path, duration = generate_pdf(nb_path, out_pdf, config=config)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 2000
    assert duration > 0


def test_generate_handout_with_slide_printer_dots_and_2up(tmp_path: Path):
    """Test handout generation with bullet points / dots note style and 2-up layout."""
    nb_path = SAMPLES_DIR / "slides_example.ipynb"
    out_pdf = tmp_path / "handout_dots_2up.pdf"

    config = NbpressConfig(
        layout=LayoutMode.HANDOUT,
        handout_note_style=HandoutNoteStyle.DOTS,
        handout_disposition=HandoutDisposition.TWO_UP,
        theme=DocTheme.MID_CENTURY,
        paper=PaperSize.A4,
        use_slide_printer_api=True,
    )

    pdf_path, duration = generate_pdf(nb_path, out_pdf, config=config)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 2000


def test_generate_mid_century_document(tmp_path: Path):
    """Test continuous document layout with Mid-Century Modern theme."""
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    out_pdf = tmp_path / "mid_century_doc.pdf"

    config = NbpressConfig(
        layout=LayoutMode.DOCUMENT,
        theme=DocTheme.MID_CENTURY,
        paper=PaperSize.A4,
        cover=True,
        toc=True,
    )

    pdf_path, duration = generate_pdf(nb_path, out_pdf, config=config)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 5000


def test_cli_build_multiple_layouts(tmp_path: Path):
    """Test CLI command with --layout multiple values and --theme mid-century."""
    nb_path = SAMPLES_DIR / "slides_example.ipynb"

    result = runner.invoke(
        app,
        [
            "build",
            str(nb_path),
            "--output",
            str(tmp_path),
            "--layout",
            "document,slides,handout",
            "--theme",
            "mid-century",
            "--handout-style",
            "grid",
        ],
    )

    assert result.exit_code == 0
    assert "Compilación completada con éxito" in result.output
    assert (tmp_path / "slides_example_doc.pdf").exists()
    assert (tmp_path / "slides_example_slides.pdf").exists()
    assert (tmp_path / "slides_example_handout.pdf").exists()


def test_slides_vertical_budgeting(tmp_path: Path):
    """Test slides layout with vertical budgeting and heading levels."""
    from pypdf import PdfReader
    from nbpress.parser import load_notebook
    from nbpress.generator import build_slides_list

    nb_path = SAMPLES_DIR / "slides_example.ipynb"
    nb = load_notebook(nb_path)
    config = NbpressConfig(
        layout=LayoutMode.SLIDES,
        cover=True,
    )
    slides = build_slides_list(nb, assets_dir=tmp_path / "assets", config=config)
    assert len(slides) >= 1
    for slide in slides:
        assert slide["title"] is not None

    out_pdf = tmp_path / "slides_budget.pdf"
    pdf_path, _ = generate_pdf(nb_path, out_pdf, config=config)
    assert pdf_path.exists()
    reader = PdfReader(pdf_path)
    # Total pages should equal cover (1) + number of slides (no overflow or orphan pages)
    assert len(reader.pages) == len(slides) + 1

