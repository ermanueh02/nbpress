"""
LaTeX to Typst math converter.
Translates inline ($...$) and display ($$...$$) LaTeX expressions into Typst math syntax.
"""

from __future__ import annotations

import re


GREEK_LETTERS = {
    r"\alpha": "alpha",
    r"\beta": "beta",
    r"\gamma": "gamma",
    r"\delta": "delta",
    r"\epsilon": "epsilon",
    r"\varepsilon": "epsilon.alt",
    r"\zeta": "zeta",
    r"\eta": "eta",
    r"\theta": "theta",
    r"\vartheta": "theta.alt",
    r"\iota": "iota",
    r"\kappa": "kappa",
    r"\lambda": "lambda",
    r"\mu": "mu",
    r"\nu": "nu",
    r"\xi": "xi",
    r"\pi": "pi",
    r"\varpi": "pi.alt",
    r"\rho": "rho",
    r"\varrho": "rho.alt",
    r"\sigma": "sigma",
    r"\varsigma": "sigma.alt",
    r"\tau": "tau",
    r"\upsilon": "upsilon",
    r"\phi": "phi",
    r"\varphi": "phi.alt",
    r"\chi": "chi",
    r"\psi": "psi",
    r"\omega": "omega",
    r"\Gamma": "Gamma",
    r"\Delta": "Delta",
    r"\Theta": "Theta",
    r"\Lambda": "Lambda",
    r"\Xi": "Xi",
    r"\Pi": "Pi",
    r"\Sigma": "Sigma",
    r"\Upsilon": "Upsilon",
    r"\Phi": "Phi",
    r"\Psi": "Psi",
    r"\Omega": "Omega",
}

MATH_SYMBOLS = {
    r"\times": " times ",
    r"\cdot": " dot ",
    r"\div": " div ",
    r"\pm": " plus.minus ",
    r"\mp": " minus.plus ",
    r"\le": " <= ",
    r"\leq": " <= ",
    r"\ge": " >= ",
    r"\geq": " >= ",
    r"\neq": " != ",
    r"\ne": " != ",
    r"\approx": " approx ",
    r"\simeq": " approx ",
    r"\lesssim": " lt.approx ",
    r"\gtrsim": " gt.approx ",
    r"\sim": " tilde ",
    r"\equiv": " equiv ",
    r"\gg": " >> ",
    r"\ll": " << ",
    r"\propto": " prop ",
    r"\parallel": " parallel ",
    r"\perp": " bot ",
    r"\oplus": " plus.o ",
    r"\otimes": " times.o ",
    r"\odot": " dot.o ",
    r"\hbar": " planck.reduce ",
    r"\ell": " ell ",
    r"\in": " in ",
    r"\notin": " in.not ",
    r"\subset": " subset ",
    r"\subseteq": " subset.eq ",
    r"\cup": " union ",
    r"\cap": " sect ",
    r"\infty": " infinity ",
    r"\partial": " diff ",
    r"\nabla": " nabla ",
    r"\forall": " forall ",
    r"\exists": " exists ",
    r"\neg": " not ",
    r"\implies": " => ",
    r"\iff": " <=> ",
    r"\longrightarrow": " --> ",
    r"\longleftarrow": " <-- ",
    r"\rightarrow": " -> ",
    r"\to": " -> ",
    r"\leftarrow": " <- ",
    r"\Rightarrow": " => ",
    r"\Leftarrow": " <= ",
    r"\Leftrightarrow": " <=> ",
    r"\dots": " ... ",
    r"\cdots": " ... ",
    r"\ldots": " ... ",
}

MATH_OPERATORS = [
    "sin", "cos", "tan", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "exp", "log", "ln", "det",
    "dim", "gcd", "hom", "ker", "deg", "arg", "min", "max", "sup", "inf"
]


def extract_balanced_group(text: str, open_pos: int) -> tuple[str, int]:
    """Extract content inside balanced { ... } starting at open_pos."""
    depth = 0
    start = open_pos + 1
    for i in range(open_pos, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
    return text[start:], len(text)


def convert_fractions(text: str) -> str:
    """Convert \\frac{num}{den} to (num) / (den), supporting nested braces."""
    while r"\frac" in text:
        idx = text.find(r"\frac")
        first_brace = text.find("{", idx)
        if first_brace == -1:
            break
        num, next_pos = extract_balanced_group(text, first_brace)
        second_brace = text.find("{", next_pos)
        if second_brace == -1:
            break
        den, end_pos = extract_balanced_group(text, second_brace)
        
        num_converted = convert_fractions(num)
        den_converted = convert_fractions(den)
        replacement = f"({num_converted}) / ({den_converted})"
        text = text[:idx] + replacement + text[end_pos:]
    return text


def convert_roots(text: str) -> str:
    """Convert \\sqrt[n]{x} and \\sqrt{x} with balanced braces."""
    # First \sqrt[n]{x}
    while r"\sqrt[" in text:
        idx = text.find(r"\sqrt[")
        close_bracket = text.find("]", idx)
        if close_bracket == -1:
            break
        n_val = text[idx + 6:close_bracket]
        first_brace = text.find("{", close_bracket)
        if first_brace == -1:
            break
        body, end_pos = extract_balanced_group(text, first_brace)
        replacement = f"root({n_val}, {body})"
        text = text[:idx] + replacement + text[end_pos:]

    # Next \sqrt{x}
    while r"\sqrt" in text:
        idx = text.find(r"\sqrt")
        first_brace = text.find("{", idx)
        if first_brace == -1 or first_brace > idx + 7:
            break
        body, end_pos = extract_balanced_group(text, first_brace)
        replacement = f"sqrt({body})"
        text = text[:idx] + replacement + text[end_pos:]
    return text


def convert_matrices(text: str) -> str:
    """Convert LaTeX matrix environments to Typst mat(...)."""
    def matrix_replacer(match: re.Match) -> str:
        env = match.group(1)
        body = match.group(2).strip()
        # rows separated by \\
        rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
        typst_rows = []
        for row in rows:
            # cells separated by &
            cells = [c.strip() for c in row.split("&")]
            typst_rows.append(", ".join(cells))
        delim = ""
        if env == "pmatrix":
            delim = 'delim: "(" '
        elif env == "bmatrix":
            delim = 'delim: "[" '
        elif env == "vmatrix":
            delim = 'delim: "|" '
        
        inner = "; ".join(typst_rows)
        if delim:
            return f"mat({delim}, {inner})"
        return f"mat({inner})"

    pattern = re.compile(
        r"\\begin\{(matrix|pmatrix|bmatrix|vmatrix)\}(.*?)\\end\{\1\}",
        re.DOTALL,
    )
    return pattern.sub(matrix_replacer, text)


def latex_to_typst_math(latex: str, is_block: bool = False) -> str:
    """
    Translates a LaTeX math string into a valid Typst math expression.
    """
    expr = latex.strip()
    if not expr:
        return ""

    # Remove enclosing $ if provided
    if expr.startswith("$$") and expr.endswith("$$"):
        expr = expr[2:-2].strip()
        is_block = True
    elif expr.startswith("$") and expr.endswith("$"):
        expr = expr[1:-1].strip()

    # Convert text environments
    expr = re.sub(r"\\text\{([^}]+)\}", r'"\1"', expr)
    expr = re.sub(r"\\mathrm\{([^}]+)\}", r'"\1"', expr)
    expr = re.sub(r"\\mathbf\{([^}]+)\}", r"bold(\1)", expr)
    expr = re.sub(r"\\mathit\{([^}]+)\}", r"italic(\1)", expr)
    expr = re.sub(r"\\mathbb\{([A-Za-z]+)\}", r"bb(\1)", expr)
    expr = re.sub(r"\\mathcal\{([A-Za-z]+)\}", r"cal(\1)", expr)

    # Matrices
    expr = convert_matrices(expr)

    # Fractions & Roots
    expr = convert_fractions(expr)
    expr = convert_roots(expr)

    # Sums, Products, Integrals
    expr = re.sub(r"\\sum_\{([^{}]+)\}\^\{([^{}]+)\}", r"sum_(\1)^(\2) ", expr)
    expr = re.sub(r"\\sum_\{([^{}]+)\}", r"sum_(\1) ", expr)
    expr = re.sub(r"\\sum(?![a-zA-Z])", "sum ", expr)

    expr = re.sub(r"\\prod_\{([^{}]+)\}\^\{([^{}]+)\}", r"product_(\1)^(\2) ", expr)
    expr = re.sub(r"\\prod_\{([^{}]+)\}", r"product_(\1) ", expr)
    expr = re.sub(r"\\prod(?![a-zA-Z])", "product ", expr)

    expr = re.sub(r"\\int_\{([^{}]+)\}\^\{([^{}]+)\}", r"integral_(\1)^(\2) ", expr)
    expr = re.sub(r"\\int_\{([^{}]+)\}", r"integral_(\1) ", expr)
    expr = re.sub(r"\\int(?![a-zA-Z])", "integral ", expr)

    expr = re.sub(r"\\lim_\{([^{}]+)\}", r"lim_(\1) ", expr)
    expr = re.sub(r"\\lim(?![a-zA-Z])", "lim ", expr)

    # Delimiters \left \right, \langle, \rangle
    expr = re.sub(r"\\(left|right)\.", "", expr)
    expr = re.sub(r"\\left\b\s*", "", expr)
    expr = re.sub(r"\\right\b\s*", "", expr)
    expr = expr.replace(r"\langle", " chevron.l ").replace(r"\rangle", " chevron.r ")
    expr = expr.replace(r"\{", "{").replace(r"\}", "}")

    # Math symbols (must precede 2-letter word splitting)
    for tex, typ in MATH_SYMBOLS.items():
        expr = re.sub(re.escape(tex) + r"(?![a-zA-Z])", typ, expr)

    # Math operators (\sin -> sin, etc.) with safe spacing
    for op in MATH_OPERATORS:
        expr = re.sub(r"\\" + op + r"(?![a-zA-Z])", f" {op} ", expr)

    # Greek letters with safe spacing
    for tex, typ in GREEK_LETTERS.items():
        expr = re.sub(re.escape(tex) + r"(?![a-zA-Z])", f" {typ} ", expr)

    # Leading superscripts or subscripts without base (e.g. ^{238}U -> ""^{238} U)
    expr = re.sub(r"(^|[\s(\[{=])(\^|_)", r'\1""\2', expr)

    # Separate adjacent single-letter particle symbols (e.g. ep -> e p, pp -> p p, ee -> e e)
    valid_2letter = {"in", "to", "pi", "mu", "xi", "nu", "ln", "bb", "eq", "ne", "lt", "gt", "le", "ge", "or", "im", "re"}
    def split_unknown_2letter(m: re.Match) -> str:
        word = m.group(0)
        if word in valid_2letter:
            return word
        return f"{word[0]} {word[1]}"

    expr = re.sub(r"\b[a-zA-Z]{2}\b", split_unknown_2letter, expr)

    # Accents with spacing when attached to characters
    expr = re.sub(r"(?<=[a-zA-Z0-9])\\bar\{([^{}]+)\}", r" macron(\1)", expr)
    expr = re.sub(r"\\bar\{([^{}]+)\}", r"macron(\1)", expr)
    expr = re.sub(r"(?<=[a-zA-Z0-9])\\hat\{([^{}]+)\}", r" hat(\1)", expr)
    expr = re.sub(r"\\hat\{([^{}]+)\}", r"hat(\1)", expr)
    expr = re.sub(r"(?<=[a-zA-Z0-9])\\vec\{([^{}]+)\}", r" arrow(\1)", expr)
    expr = re.sub(r"\\vec\{([^{}]+)\}", r"arrow(\1)", expr)
    expr = re.sub(r"(?<=[a-zA-Z0-9])\\tilde\{([^{}]+)\}", r" tilde(\1)", expr)
    expr = re.sub(r"\\tilde\{([^{}]+)\}", r"tilde(\1)", expr)
    expr = re.sub(r"\\dot\{([^{}]+)\}", r"dot(\1)", expr)
    expr = re.sub(r"\\ddot\{([^{}]+)\}", r"dot.double(\1)", expr)

    # Replace remaining simple curly braces around sub/superscripts e.g. x^{2} -> x^2, x_{ij} -> x_(ij)
    expr = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", expr)
    expr = re.sub(r"_\{([^{}]+)\}", r"_(\1)", expr)

    # Spaces & LaTeX horizontal spacing
    expr = re.sub(r"\\[,; ]", " ", expr)
    expr = expr.replace(r"\quad", "  ").replace(r"\qquad", "    ")

    # Clean any residual backslashes before words so Typst never encounters unknown commands
    expr = re.sub(r"\\([a-zA-Z]+)", r" \1 ", expr)

    # Normalize multiple spaces
    expr = re.sub(r"[ \t]+", " ", expr).strip()
    if is_block:
        return f"$ {expr} $"
    return f"${expr}$"
