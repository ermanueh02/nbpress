"""
nbpress: Transform Jupyter Notebooks (.ipynb) into editorial-grade, print-ready PDFs.
"""

__version__ = "0.1.0"
__author__ = "nbpress contributors"

from nbpress.config import NbpressConfig, LayoutMode, PaperSize
from nbpress.generator import generate_pdf, generate_typst_source

__all__ = [
    "__version__",
    "NbpressConfig",
    "LayoutMode",
    "PaperSize",
    "generate_pdf",
    "generate_typst_source",
]
