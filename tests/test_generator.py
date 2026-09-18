"""
End-to-end tests for PDF generation across all layout modes.
"""

from pathlib import Path
import pytest
from nbpress.config import LayoutMode, NbpressConfig, PaperSize
from nbpress.generator import generate_pdf


SAMPLES_DIR = Path(__file__).parent / "sample_notebooks"


def test_generate_document_layout(tmp_path: Path):
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    out_pdf = tmp_path / "document_test.pdf"

    config = NbpressConfig(
        layout=LayoutMode.DOCUMENT,
        paper=PaperSize.A4,
        cover=True,
        toc=True,
    )
    pdf_path, duration = generate_pdf(nb_path, out_pdf, config=config)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 5000  # Non-trivial PDF with charts & tables
    assert duration > 0


def test_generate_slides_layout(tmp_path: Path):
    nb_path = SAMPLES_DIR / "slides_example.ipynb"
    out_pdf = tmp_path / "slides_test.pdf"

    config = NbpressConfig(
        layout=LayoutMode.SLIDES,
        cover=True,
    )
    pdf_path, duration = generate_pdf(nb_path, out_pdf, config=config)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000


def test_generate_handout_layout(tmp_path: Path):
    nb_path = SAMPLES_DIR / "slides_example.ipynb"
    out_pdf = tmp_path / "handout_test.pdf"

    config = NbpressConfig(
        layout=LayoutMode.HANDOUT,
        paper=PaperSize.A4,
        handout_note_lines=6,
    )
    pdf_path, duration = generate_pdf(nb_path, out_pdf, config=config)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000


def test_generate_cheatsheet_layout(tmp_path: Path):
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    out_pdf = tmp_path / "cheatsheet_test.pdf"

    config = NbpressConfig(
        layout=LayoutMode.CHEATSHEET,
        paper=PaperSize.A4,
        eco=True,
        gutter="1.5cm",
    )
    pdf_path, duration = generate_pdf(nb_path, out_pdf, config=config)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 5000
