"""
Tests for CLI interface using typer.testing.CliRunner.
"""

from pathlib import Path
from typer.testing import CliRunner
from nbpress.cli import app


runner = CliRunner()
SAMPLES_DIR = Path(__file__).parent / "sample_notebooks"


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "nbpress" in result.output
    assert "Typst Engine" in result.output


def test_cli_info():
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    result = runner.invoke(app, ["info", str(nb_path)])
    assert result.exit_code == 0
    assert "Analisis Cuantitativo" in result.output
    assert "Markdown" in result.output
    assert "Código" in result.output


def test_cli_build(tmp_path: Path):
    nb_path = SAMPLES_DIR / "complete_features.ipynb"
    out_pdf = tmp_path / "cli_output.pdf"
    
    result = runner.invoke(app, [
        "build",
        str(nb_path),
        "-o", str(out_pdf),
        "--layout", "document",
        "--eco",
    ])
    assert result.exit_code == 0
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 5000
