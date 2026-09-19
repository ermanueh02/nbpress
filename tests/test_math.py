"""
Tests for LaTeX to Typst math conversion.
"""

from nbpress.processors.math import (
    convert_fractions,
    convert_matrices,
    convert_roots,
    latex_to_typst_math,
)


def test_convert_fractions():
    latex = r"\frac{a}{b}"
    assert convert_fractions(latex) == "(a) / (b)"

    nested = r"\frac{1}{\sigma \sqrt{2\pi}}"
    converted = convert_fractions(nested)
    assert converted.startswith("(1) / (")


def test_convert_roots():
    simple = r"\sqrt{x}"
    assert convert_roots(simple) == "sqrt(x)"

    nth = r"\sqrt[3]{8}"
    assert convert_roots(nth) == "root(3, 8)"


def test_convert_matrices():
    mat_tex = r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}"
    typst_mat = convert_matrices(mat_tex)
    assert typst_mat == 'mat(delim: "(" , a, b; c, d)'


def test_latex_to_typst_math():
    # Greek letters
    assert latex_to_typst_math(r"\alpha + \beta = \gamma") == "$alpha + beta = gamma$"

    # Sums and integrals
    integral = latex_to_typst_math(r"\int_{0}^{\infty} f(x) dx", is_block=True)
    assert "integral_(0)^(" in integral
    assert "infinity" in integral

    # Bold vectors/matrices
    bold_vec = latex_to_typst_math(r"\mathbf{X}^T \mathbf{X}")
    assert "bold(X)^T" in bold_vec

    # Partials, boxed equations and Planck constant
    physics = latex_to_typst_math(r"\partial_\mu j^\mu = 0, \hbar, \boxed{E = mc^2}")
    assert "partial" in physics
    assert "h.bar" in physics
    assert "rect(" in physics

    # Multi-letter indices
    indices = latex_to_typst_math(r"\epsilon_{ijk}")
    assert "_(i j k)" in indices
