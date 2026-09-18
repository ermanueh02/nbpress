"""
Tests for notebook parsing and normalization.
"""

from pathlib import Path
import pytest
from nbpress.models import CellType, OutputType, SlideType
from nbpress.parser import extract_heading_info, load_notebook, parse_slide_type


SAMPLES_DIR = Path(__file__).parent / "sample_notebooks"


def test_extract_heading_info():
    level, text = extract_heading_info("# My Great Title\nSome content")
    assert level == 1
    assert text == "My Great Title"

    level2, text2 = extract_heading_info("### Section 3.2 ###\nMore content")
    assert level2 == 3
    assert text2 == "Section 3.2"

    none_lvl, none_txt = extract_heading_info("Just a plain paragraph without header.")
    assert none_lvl is None
    assert none_txt is None


def test_parse_slide_type():
    assert parse_slide_type({"slideshow": {"slide_type": "slide"}}) == SlideType.SLIDE
    assert parse_slide_type({"slideshow": {"slide_type": "subslide"}}) == SlideType.SUBSLIDE
    assert parse_slide_type({}) == SlideType.NONE


def test_load_complete_features_notebook():
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    assert nb_path.exists(), "Sample notebook does not exist"

    doc = load_notebook(nb_path)
    assert doc.title == "Analisis Cuantitativo y Modelado Estadistico"
    assert len(doc.authors) >= 1
    assert len(doc.cells) == 5

    # Check cell types
    markdown_cells = [c for c in doc.cells if c.cell_type == CellType.MARKDOWN]
    code_cells = [c for c in doc.cells if c.cell_type == CellType.CODE]
    assert len(markdown_cells) == 2
    assert len(code_cells) == 3

    # Check outputs
    plot_cell = code_cells[0]
    assert len(plot_cell.outputs) == 1
    assert plot_cell.outputs[0].has_image

    df_cell = code_cells[1]
    assert len(df_cell.outputs) == 1
    assert df_cell.outputs[0].has_html_table


def test_load_slides_notebook():
    nb_path = SAMPLES_DIR / "slides_example.ipynb"
    doc = load_notebook(nb_path)
    assert doc.title == "Introduccion al Aprendizaje Automatico"
    slide_starters = [c for c in doc.cells if c.is_slide_starter]
    assert len(slide_starters) >= 2
