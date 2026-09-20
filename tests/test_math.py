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
    assert "planck" in physics
    assert "#box(" in physics

    # Multi-letter indices
    indices = latex_to_typst_math(r"\epsilon_{ijk}")
    assert "_(i j k)" in indices


def test_advanced_math_constructs():
    # Operatorname (diag)
    op_tex = latex_to_typst_math(r"\operatorname{diag}(1, -1, -1, -1)")
    assert 'op("diag")' in op_tex

    # Spacing commands
    space_tex = latex_to_typst_math(r"a \quad b \qquad c")
    assert "quad" in space_tex
    assert "wide" in space_tex

    # Align environments
    align_tex = latex_to_typst_math(
        r"\begin{align} A &= B \\ C &= D \end{align}", is_block=True
    )
    assert r"\begin{align}" not in align_tex
    assert "A &= B \\ C &= D" in align_tex

    # Boxed align environment
    boxed_align = latex_to_typst_math(
        r"\boxed{\begin{align} (E - \mathbf{p}) u = 0 \\ (E + \mathbf{p}) v = 0 \end{align}}",
        is_block=True,
    )
    assert "#box(stroke:" in boxed_align
    assert "bold(p)" in boxed_align

    # Arrows and overset
    arrow_tex = latex_to_typst_math(r"u_L \xrightarrow{\kappa \to 1} u_R")
    assert "limits(arrow.r.long)^( kappa -> 1)" in arrow_tex

    overset_tex = latex_to_typst_math(r"u_L \overset{P}{\longleftrightarrow} u_R")
    assert "limits( arrow.l.r.long )^(P)" in overset_tex

    # Unbraced accents
    accent_tex = latex_to_typst_math(r"\bar\Psi + \hat p")
    assert "macron( Psi )" in accent_tex or "macron(Psi)" in accent_tex
    assert "hat(p)" in accent_tex

    # Attached bold token like -i\mathbf{\nabla}
    nabla_tex = latex_to_typst_math(r"-i\mathbf{\nabla}")
    assert "bold( nabla )" in nabla_tex or "bold(nabla)" in nabla_tex
    assert "b o l d" not in nabla_tex
