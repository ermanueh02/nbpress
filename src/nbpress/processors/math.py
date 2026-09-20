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
    r"\hbar": " planck ",
    r"\ell": " ell ",
    r"\in": " in ",
    r"\notin": " in.not ",
    r"\subset": " subset ",
    r"\subseteq": " subset.eq ",
    r"\cup": " union ",
    r"\cap": " inter ",
    r"\infty": " infinity ",
    r"\partial": " partial ",
    r"\nabla": " nabla ",
    r"\forall": " forall ",
    r"\exists": " exists ",
    r"\neg": " not ",
    r"\implies": " => ",
    r"\iff": " <=> ",
    r"\longleftrightarrow": " arrow.l.r.long ",
    r"\leftrightarrow": " arrow.l.r ",
    r"\longrightarrow": " --> ",
    r"\longleftarrow": " <-- ",
    r"\rightarrow": " -> ",
    r"\to": " -> ",
    r"\leftarrow": " <- ",
    r"\Rightarrow": " => ",
    r"\Leftarrow": " <= ",
    r"\Leftrightarrow": " <=> ",
    r"\dagger": " dagger ",
    r"\star": " star ",
    r"\bullet": " bullet ",
    r"\dots": " ... ",
    r"\cdots": " ... ",
    r"\ldots": " ... ",
}

MATH_OPERATORS = [
    "sin", "cos", "tan", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "exp", "log", "ln", "det",
    "dim", "gcd", "hom", "ker", "deg", "arg", "min", "max", "sup", "inf"
]

VALID_MATH_WORDS = {
    # Token placeholders
    "MATHSTR", "NB", "BOXED", "TOKEN", "LINEBREAK",
    # Greek letters (lowercase)
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
    "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    # Greek letters (uppercase)
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon",
    "Phi", "Psi", "Omega",
    # Math operators and functions
    "sin", "cos", "tan", "cot", "sec", "csc",
    "arcsin", "arccos", "arctan", "arccot", "arcsec", "arccsc",
    "sinh", "cosh", "tanh", "coth", "sech", "csch",
    "exp", "log", "ln", "lg", "det", "dim", "gcd", "lcm", "hom", "ker",
    "deg", "arg", "min", "max", "sup", "inf", "lim", "mod",
    "integral", "sum", "product", "op",
    # Structure, styling, boxes
    "bold", "italic", "rect", "sqrt", "root", "mat", "vec", "arrow",
    "hat", "macron", "tilde", "dot", "cancel", "underline", "overline",
    "bb", "cal", "frak", "mono", "sans", "display", "inline", "script",
    "box", "stroke", "inset", "radius", "baseline",
    # Symbols & relations
    "times", "plus", "minus", "div", "approx", "equiv", "nabla", "partial",
    "dif", "dagger", "star", "inter", "union", "subset", "in", "to",
    "infinity", "dots", "forall", "exists", "not", "chevron", "prime",
    "parallel", "prop", "bot", "top", "vert", "delim", "cases", "bullet",
    # Modifiers & spacing
    "alt", "double", "bar", "reduce", "long", "quad", "wide", "limits", "planck",
    # Logic / relations
    "eq", "ne", "lt", "gt", "le", "ge", "or", "and", "xor", "im", "re"
}


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
        rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
        typst_rows = []
        for row in rows:
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


def convert_align_environments(text: str) -> str:
    """Strip align, aligned, gather, and equation environments, converting \\\\ to \\."""
    text = re.sub(r"\\(nonumber|notag)", "", text)
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = re.sub(
        r"\\begin\{(align\*?|aligned|gather\*?|equation\*?)\}",
        "",
        text,
    )
    text = re.sub(
        r"\\end\{(align\*?|aligned|gather\*?|equation\*?)\}",
        "",
        text,
    )
    # Convert \\ outside matrices (which have been converted already) to a placeholder
    text = re.sub(r"\\\\", r" __NB_LINEBREAK__ ", text)
    return text


def convert_arrows_and_over(text: str) -> str:
    """Convert \\xrightarrow[sub]{sup}, \\overset{top}{base}, and \\underset{bot}{base}."""
    while r"\xrightarrow[" in text:
        idx = text.find(r"\xrightarrow[")
        close_bracket = text.find("]", idx)
        if close_bracket == -1:
            break
        sub_val = text[idx + 12:close_bracket]
        first_brace = text.find("{", close_bracket)
        if first_brace == -1:
            break
        sup_val, end_pos = extract_balanced_group(text, first_brace)
        replacement = f" limits(arrow.r.long)_({sub_val})^({sup_val}) "
        text = text[:idx] + replacement + text[end_pos:]

    while r"\xrightarrow" in text:
        idx = text.find(r"\xrightarrow")
        first_brace = text.find("{", idx)
        if first_brace == -1 or first_brace > idx + 13:
            break
        sup_val, end_pos = extract_balanced_group(text, first_brace)
        replacement = f" limits(arrow.r.long)^({sup_val}) "
        text = text[:idx] + replacement + text[end_pos:]

    while r"\overset" in text:
        idx = text.find(r"\overset")
        first_brace = text.find("{", idx)
        if first_brace == -1 or first_brace > idx + 9:
            break
        top_val, next_pos = extract_balanced_group(text, first_brace)
        second_brace = text.find("{", next_pos)
        if second_brace == -1:
            break
        base_val, end_pos = extract_balanced_group(text, second_brace)
        replacement = f" limits({base_val})^({top_val}) "
        text = text[:idx] + replacement + text[end_pos:]

    while r"\underset" in text:
        idx = text.find(r"\underset")
        first_brace = text.find("{", idx)
        if first_brace == -1 or first_brace > idx + 10:
            break
        bot_val, next_pos = extract_balanced_group(text, first_brace)
        second_brace = text.find("{", next_pos)
        if second_brace == -1:
            break
        base_val, end_pos = extract_balanced_group(text, second_brace)
        replacement = f" limits({base_val})_({bot_val}) "
        text = text[:idx] + replacement + text[end_pos:]

    return text


def extract_boxed_groups(text: str) -> tuple[str, list[str]]:
    """Extract \\boxed{expr} into placeholder tokens to protect from word splitting."""
    boxed_bodies: list[str] = []
    while r"\boxed" in text:
        idx = text.find(r"\boxed")
        first_brace = text.find("{", idx)
        if first_brace == -1 or first_brace > idx + 8:
            break
        body, end_pos = extract_balanced_group(text, first_brace)
        placeholder = f"__NB_BOXED_TOKEN_{len(boxed_bodies)}__"
        boxed_bodies.append(body)
        text = text[:idx] + f" {placeholder} " + text[end_pos:]
    return text, boxed_bodies


def _translate_math_body(expr: str, is_block: bool = False) -> str:
    """Internal recursive engine translating math content."""
    # 1. Boxed equations: extract placeholders to protect from split_unknown_words
    expr, boxed_bodies = extract_boxed_groups(expr)
    converted_boxed = [
        _translate_math_body(b, is_block=is_block) for b in boxed_bodies
    ]

    # 2. Text and style environments (with padding so tokens never fuse)
    expr = re.sub(r"\\text(normal)?\{([^}]+)\}", r' "\2" ', expr)
    expr = re.sub(r"\\mathrm\{([^}]+)\}", r' "\1" ', expr)
    expr = re.sub(r"\\operatorname\{([^}]+)\}", r' op("\1") ', expr)
    expr = re.sub(r"\\(mathbf|boldsymbol|bm)\{([^}]+)\}", r" bold(\2) ", expr)
    expr = re.sub(r"\\mathit\{([^}]+)\}", r" italic(\1) ", expr)
    expr = re.sub(r"\\mathbb\{([A-Za-z]+)\}", r" bb(\1) ", expr)
    expr = re.sub(r"\\mathcal\{([A-Za-z]+)\}", r" cal(\1) ", expr)
    expr = re.sub(r"\\underline\{([^}]+)\}", r" underline(\1) ", expr)
    expr = re.sub(r"\\overline\{([^}]+)\}", r" overline(\1) ", expr)
    expr = re.sub(r"\\cancel\{([^}]+)\}", r" cancel(\1) ", expr)

    # 3. Arrows and overset
    expr = convert_arrows_and_over(expr)

    # 4. Matrices (must run before align to handle matrix \\ and &)
    expr = convert_matrices(expr)

    # 5. Align environments and linebreaks
    expr = convert_align_environments(expr)

    # 6. Fractions & Roots
    expr = convert_fractions(expr)
    expr = convert_roots(expr)

    # 7. Sums, Products, Integrals, Limits
    expr = re.sub(r"\\sum_\{([^{}]+)\}\^\{([^{}]+)\}", r" sum_(\1)^(\2) ", expr)
    expr = re.sub(r"\\sum_\{([^{}]+)\}", r" sum_(\1) ", expr)
    expr = re.sub(r"\\sum(?![a-zA-Z])", " sum ", expr)

    expr = re.sub(r"\\prod_\{([^{}]+)\}\^\{([^{}]+)\}", r" product_(\1)^(\2) ", expr)
    expr = re.sub(r"\\prod_\{([^{}]+)\}", r" product_(\1) ", expr)
    expr = re.sub(r"\\prod(?![a-zA-Z])", " product ", expr)

    expr = re.sub(r"\\int_\{([^{}]+)\}\^\{([^{}]+)\}", r" integral_(\1)^(\2) ", expr)
    expr = re.sub(r"\\int_\{([^{}]+)\}", r" integral_(\1) ", expr)
    expr = re.sub(r"\\int(?![a-zA-Z])", " integral ", expr)

    expr = re.sub(r"\\lim_\{([^{}]+)\}", r" lim_(\1) ", expr)
    expr = re.sub(r"\\lim(?![a-zA-Z])", " lim ", expr)

    # 8. Delimiters \left \right, \langle, \rangle
    expr = re.sub(r"\\(left|right)\.", "", expr)
    expr = re.sub(r"\\left\b\s*", "", expr)
    expr = re.sub(r"\\right\b\s*", "", expr)
    expr = expr.replace(r"\langle", " chevron.l ").replace(r"\rangle", " chevron.r ")
    expr = expr.replace(r"\{", "{").replace(r"\}", "}")

    # 9. Math symbols
    for tex, typ in MATH_SYMBOLS.items():
        expr = re.sub(re.escape(tex) + r"(?![a-zA-Z])", typ, expr)

    # 10. Math operators
    for op in MATH_OPERATORS:
        expr = re.sub(r"\\" + op + r"(?![a-zA-Z])", f" {op} ", expr)

    # 10. Accents (both braced and unbraced, before Greek letters so \bar\Psi matches cleanly)
    for tex_cmd, typ_func in [
        ("bar", "macron"),
        ("hat", "hat"),
        ("vec", "arrow"),
        ("tilde", "tilde"),
        ("dot", "dot"),
        ("ddot", "dot.double"),
    ]:
        expr = re.sub(rf"\\{tex_cmd}\{{([^{{}}]+)\}}", rf" {typ_func}(\1) ", expr)
        expr = re.sub(rf"\\{tex_cmd}\s*(\\[a-zA-Z]+|[a-zA-Z0-9])", rf" {typ_func}(\1) ", expr)

    # 11. Greek letters
    for tex, typ in GREEK_LETTERS.items():
        expr = re.sub(re.escape(tex) + r"(?![a-zA-Z])", f" {typ} ", expr)

    # 12. Attach superscripts/subscripts without extra space, or pad leading sub/superscripts
    expr = re.sub(r"\s+(\^|_)", r"\1", expr)
    expr = re.sub(r"(^|[(\[{=])(\^|_)", r'\1""\2', expr)

    # 14. Sub/superscripts e.g. x^{2} -> x^(2), x_{ij} -> x_(ij)
    expr = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", expr)
    expr = re.sub(r"_\{([^{}]+)\}", r"_(\1)", expr)

    # 15. Spacing commands before word splitting
    expr = re.sub(r"\\[,; ]", " ", expr)
    expr = re.sub(r"\\qquad(?![a-zA-Z])", " wide ", expr)
    expr = re.sub(r"\\(quad|enskip|enspace)(?![a-zA-Z])", " quad ", expr)

    # 16. Protect quoted strings from word splitting
    str_tokens = []
    def save_str(m: re.Match) -> str:
        idx = len(str_tokens)
        str_tokens.append(m.group(0))
        return f"__MATHSTR_{idx}__"

    expr = re.sub(r'"[^"]*"', save_str, expr)

    # 17. Separate adjacent single-letter symbols and indices
    def split_unknown_words(m: re.Match) -> str:
        word = m.group(0)
        if word in VALID_MATH_WORDS:
            return word
        return " ".join(list(word))

    expr = re.sub(r"(?<![a-zA-Z])[a-zA-Z]{2,}(?![a-zA-Z])", split_unknown_words, expr)

    # Restore quoted strings
    for i, token in enumerate(str_tokens):
        expr = expr.replace(f"__MATHSTR_{i}__", token)

    # 18. Clean residual backslashes
    expr = re.sub(r"\\([a-zA-Z]+)", r" \1 ", expr)

    # 19. Restore boxed placeholders
    for i, body in enumerate(converted_boxed):
        if is_block:
            box_code = f"#box(stroke: 0.75pt, inset: 6pt, radius: 2pt)[$ {body} $]"
        else:
            box_code = f"#box(stroke: 0.75pt, inset: (x: 4pt, y: 3pt), baseline: 20%)[$ {body} $]"
        expr = expr.replace(f"__NB_BOXED_TOKEN_{i}__", box_code)

    # 20. Restore line breaks with proper spacing
    expr = expr.replace("__NB_LINEBREAK__", " \\ ")

    # 21. Clean up trailing backslashes & normalize spaces
    expr = re.sub(r"[ \t]+", " ", expr).strip()
    expr = re.sub(r"\\\s*$", "", expr).strip()
    return expr


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

    body = _translate_math_body(expr, is_block=is_block)
    if is_block:
        return f"$ {body} $"
    return f"${body}$"
