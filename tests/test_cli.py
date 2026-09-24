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


def test_ensure_slide_printer_already_installed():
    from nbpress.deps import ensure_slide_printer
    # Since slide_printer is installed, it should return True immediately
    assert ensure_slide_printer() is True


def test_ensure_slide_printer_installs_from_git(monkeypatch):
    import builtins
    from unittest.mock import MagicMock
    from nbpress.deps import ensure_slide_printer, SLIDE_PRINTER_GIT_URL

    real_import = builtins.__import__
    def fake_import(name, *args, **kwargs):
        if name == "slide_printer":
            raise ImportError("No module named 'slide_printer'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    mock_check_call = MagicMock(return_value=0)
    monkeypatch.setattr("subprocess.check_call", mock_check_call)

    result = ensure_slide_printer()
    assert result is True
    assert mock_check_call.called
    called_cmd = mock_check_call.call_args[0][0]
    assert SLIDE_PRINTER_GIT_URL in called_cmd


def test_cli_web_help():
    result = runner.invoke(app, ["web", "--help"])
    assert result.exit_code == 0
    assert "estudio web interactivo" in result.output
    assert "--port" in result.output
    assert "--host" in result.output


def test_web_directory_exists():
    from nbpress import cli
    pkg_web = Path(cli.__file__).resolve().parent / "web"
    assert pkg_web.is_dir()
    assert (pkg_web / "index.html").is_file()
    assert (pkg_web / "css" / "style.css").is_file()
    assert (pkg_web / "js" / "app.js").is_file()
    assert (pkg_web / "js" / "engine.js").is_file()

