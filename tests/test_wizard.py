"""
Tests for interactive terminal wizard (Slide-Printer Wizard 4.2.0).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from nbpress.cli import app
from nbpress.config import LayoutMode, NbpressConfig, PaperSize
from nbpress.wizard import find_notebooks, run_wizard

runner = CliRunner()
SAMPLES_DIR = Path(__file__).parent / "sample_notebooks"


def test_find_notebooks(tmp_path: Path):
    # Create dummy structure
    (tmp_path / "valid.ipynb").write_text("{}", encoding="utf-8")
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "nested.ipynb").write_text("{}", encoding="utf-8")
    
    # Ignored directory
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "ignored.ipynb").write_text("{}", encoding="utf-8")

    found = find_notebooks(tmp_path)
    names = [p.name for p in found]
    assert "valid.ipynb" in names
    assert "nested.ipynb" in names
    assert "ignored.ipynb" not in names


def test_wizard_cli_command_quit():
    # Test quitting immediately at prompt
    result = runner.invoke(app, ["wizard"], input="q\n")
    assert result.exit_code == 0
    assert "SLIDE-PRINTER WIZARD" in result.output
    assert "Asistente finalizado" in result.output or "PASO 1" in result.output


def test_wizard_full_flow(tmp_path: Path):
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    out_pdf = tmp_path / "wizard_output.pdf"

    # Simulate user responses for each step:
    # 1. Enter path to notebook (manual path)
    # 2. Keep detected title/author? No customization (n)
    # 3. Layout: 1 (Document)
    # 4. Paper: 1 (A4)
    #    Eco: y
    #    Gutter: 2 (1.0 cm)
    # 5. Show code: y
    #    Line numbers: y
    #    Cover: y
    #    TOC: y
    #    Output path: str(out_pdf)
    #    Keep typ: n
    # 6. Proceed compilation: y
    # 8. Post-action: 4 (Exit)
    
    inputs = [
        str(nb_path),     # Step 1: Notebook path
        "n",              # Step 2: Override metadata? (No)
        "1",              # Step 3: Layout (Document)
        "1",              # Step 3.5: Theme (Classic Editorial)
        "1",              # Step 4: Paper (A4)
        "y",              # Step 4: Eco mode (Yes)
        "2",              # Step 4: Gutter (1.0cm)
        "y",              # Step 5: Show code (Yes)
        "y",              # Step 5: Line numbers (Yes)
        "y",              # Step 5: Cover (Yes)
        "y",              # Step 5: TOC (Yes)
        str(out_pdf),     # Step 5: Output path
        "n",              # Step 5: Keep typ (No)
        "y",              # Step 6: Proceed (Yes)
        "4",              # Step 8: Post action (Exit)
    ]
    
    with patch("nbpress.wizard.find_notebooks", return_value=[]):
        result = runner.invoke(app, ["wizard"], input="\n".join(inputs) + "\n")
        assert result.exit_code == 0
        assert "SLIDE-PRINTER WIZARD" in result.output
        assert "Compilación Finalizada" in result.output
        assert out_pdf.exists()
        assert out_pdf.stat().st_size > 5000


def test_wizard_slides_flow(tmp_path: Path):
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    out_pdf = tmp_path / "wizard_slides_output.pdf"

    inputs = [
        str(nb_path),     # Step 1: Notebook path
        "n",              # Step 2: Override metadata? (No)
        "2",              # Step 3: Layout (Slides 16:9)
        "2",              # Step 3.5: Theme (Mid-Century Modern)
        "n",              # Step 4: Eco mode (No)
        "y",              # Step 5: Show code (Yes)
        "y",              # Step 5: Line numbers (Yes)
        str(out_pdf),     # Step 5: Output path
        "n",              # Step 5: Keep typ (No)
        "y",              # Step 6: Proceed (Yes)
        "4",              # Step 8: Post action (Exit)
    ]

    with patch("nbpress.wizard.find_notebooks", return_value=[]):
        result = runner.invoke(app, ["wizard"], input="\n".join(inputs) + "\n")
        assert result.exit_code == 0
        assert "Compilación Finalizada" in result.output
        assert out_pdf.exists()
        assert out_pdf.stat().st_size > 5000
