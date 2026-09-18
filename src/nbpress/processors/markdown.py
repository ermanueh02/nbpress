"""
Markdown to Typst processor for Jupyter Notebook markdown cells.
"""

from __future__ import annotations

import re
from typing import List
from nbpress.processors.math import latex_to_typst_math


def escape_typst_text(text: str) -> str:
    """Escape special Typst characters that could trigger syntax errors in plain text."""
    # We do NOT escape if it's already markdown/typst markup
    # Escape standalone hash symbols (# followed by non-typst commands)
    text = re.sub(r"#(?![a-zA-Z0-9_\-\[])", r"\#", text)
    # Escape standalone at signs (@)
    text = re.sub(r"@(?=[a-zA-Z0-9_])", r"\@", text)
    return text


def convert_table(lines: List[str]) -> str:
    """Convert a GFM markdown table to a Typst #table(...) block."""
    if len(lines) < 2:
        return "\n".join(lines)

    header_line = lines[0]
    separator_line = lines[1]
    data_lines = lines[2:]

    # Parse header cells
    headers = [c.strip() for c in header_line.strip().strip("|").split("|")]
    num_cols = len(headers)
    if num_cols == 0:
        return "\n".join(lines)

    typst_code = [f"#table(\n  columns: {num_cols},"]
    typst_code.append("  fill: (col, row) => if row == 0 { rgb(\"f1f3f5\") } else if calc.even(row) { rgb(\"fafbfc\") } else { none },")
    typst_code.append("  stroke: (col, row) => if row == 0 { (bottom: 1.5pt + rgb(\"adb5bd\")) } else { 0.5pt + rgb(\"dee2e6\") },")
    
    # Headers in bold
    for h in headers:
        clean_h = process_inline_markdown(h)
        typst_code.append(f"  [* {clean_h} *],")

    # Rows
    for row_line in data_lines:
        row_line = row_line.strip()
        if not row_line.startswith("|") and "|" not in row_line:
            continue
        cells = [c.strip() for c in row_line.strip().strip("|").split("|")]
        # Pad or trim to num_cols
        while len(cells) < num_cols:
            cells.append("")
        cells = cells[:num_cols]
        for c in cells:
            clean_c = process_inline_markdown(c)
            typst_code.append(f"  [{clean_c}],")

    typst_code.append(")\n")
    return "\n".join(typst_code)


def process_inline_markdown(text: str) -> str:
    """Process inline formatting like bold, italic, code, links, and inline math."""
    # 1. Protect inline math ($...$) before processing other markdown
    math_tokens = []
    def save_inline_math(match: re.Match) -> str:
        idx = len(math_tokens)
        math_tokens.append(latex_to_typst_math(match.group(0), is_block=False))
        return f"@@@MATH_INLINE_TOKEN_{idx}@@@"

    # Match $...$ but avoid $$...$$
    text = re.sub(r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)", save_inline_math, text)

    # 2. Protect inline code (`...`)
    code_tokens = []
    def save_inline_code(match: re.Match) -> str:
        idx = len(code_tokens)
        code_tokens.append(match.group(0))
        return f"@@@CODE_INLINE_TOKEN_{idx}@@@"

    text = re.sub(r"`([^`]+)`", save_inline_code, text)

    # 3. Bold & Italic (protect bold so italic doesn't match single asterisks)
    bold_tokens = []
    def save_bold(match: re.Match) -> str:
        idx = len(bold_tokens)
        bold_tokens.append(f"*{match.group(1)}*")
        return f"@@@BOLD_TOKEN_{idx}@@@"

    text = re.sub(r"\*\*([^\*]+)\*\*", save_bold, text)
    text = re.sub(r"__([^_]+)__", save_bold, text)

    # Italic *text* or _text_ -> _text_
    text = re.sub(r"(?<!\*)\*([^\*]+)\*(?!\*)", r"_\1_", text)
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"_\1_", text)

    # Restore bold tokens
    for i, token in enumerate(bold_tokens):
        text = text.replace(f"@@@BOLD_TOKEN_{i}@@@", token)

    # Images in markdown: ![alt](url) -> MUST be processed BEFORE [label](url)
    def render_md_img(match: re.Match) -> str:
        alt = match.group(1).strip()
        url = match.group(2).strip()
        url = url.strip('"\'')
        if alt:
            clean_alt = process_inline_markdown(alt)
            return f'#nb-image("{url}", caption: [{clean_alt}])'
        return f'#nb-image("{url}")'

    text = re.sub(r"!\[(.*?)\]\((.*?)\)", render_md_img, text)

    # HTML <img ...> tags
    def render_html_img(match: re.Match) -> str:
        tag = match.group(0)
        src_m = re.search(r'src=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        if not src_m:
            return ""
        url = src_m.group(1).strip()
        width_m = re.search(r'width\s*=\s*["\']?(\d+%?|\d+px)["\']?', tag, re.IGNORECASE)
        width_arg = ""
        if width_m:
            w_val = width_m.group(1).replace("px", "pt")
            if not w_val.endswith("%") and not w_val.endswith("pt"):
                w_val = f"{w_val}pt"
            width_arg = f", width: {w_val}"
        return f'#nb-image("{url}"{width_arg})'

    text = re.sub(r"<img\s+[^>]*>", render_html_img, text, flags=re.IGNORECASE)

    # Clean HTML container tags
    text = re.sub(r"<\/?(div|center|span|font|p|section|article)[^>]*>", "", text, flags=re.IGNORECASE)

    # Strikethrough ~~text~~
    text = re.sub(r"~~([^~]+)~~", r"#strike[\1]", text)

    # Links [label](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'#link("\2")[\1]', text)

    # Clean simple HTML formatting tags
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<hr\s*/?>", "\n#line(length: 100%, stroke: 0.5pt + rgb(\"dee2e6\"))\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<b>(.*?)</b>", r"*\1*", text, flags=re.IGNORECASE)
    text = re.sub(r"<strong>(.*?)</strong>", r"*\1*", text, flags=re.IGNORECASE)
    text = re.sub(r"<i>(.*?)</i>", r"_\1_", text, flags=re.IGNORECASE)
    text = re.sub(r"<em>(.*?)</em>", r"_\1_", text, flags=re.IGNORECASE)
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE)

    # Restore inline code tokens
    for i, token in enumerate(code_tokens):
        text = text.replace(f"@@@CODE_INLINE_TOKEN_{i}@@@", token)

    # Restore inline math tokens
    for i, token in enumerate(math_tokens):
        text = text.replace(f"@@@MATH_INLINE_TOKEN_{i}@@@", token)

    return text


def markdown_to_typst(source: str) -> str:
    """
    Convert a Jupyter Markdown cell's text into Typst formatted markup.
    """
    if not source.strip():
        return ""

    # First, handle multi-line display math $$...$$ (cleaning any blockquote > markers inside)
    display_math_tokens = []
    def save_display_math(match: re.Match) -> str:
        idx = len(display_math_tokens)
        raw_tex = match.group(1)
        # Strip leading blockquote markers if inside a quote
        clean_tex = re.sub(r"^\s*>\s?", "", raw_tex, flags=re.MULTILINE)
        typst_math = latex_to_typst_math(clean_tex, is_block=True)
        display_math_tokens.append(f"\n{typst_math}\n")
        return f"@@@DISPLAY_MATH_TOKEN_{idx}@@@"

    source = re.sub(r"\$\$(.*?)\$\$", save_display_math, source, flags=re.DOTALL)

    lines = source.splitlines()
    output_lines: List[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # Check for Display Math placeholder
        if "@@@DISPLAY_MATH_TOKEN_" in line:
            for idx, dmath in enumerate(display_math_tokens):
                line = line.replace(f"@@@DISPLAY_MATH_TOKEN_{idx}@@@", dmath)
            output_lines.append(line)
            i += 1
            continue

        # Check for Fenced Code Block
        if line.strip().startswith("```"):
            code_block = [line]
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_block.append(lines[i])
                i += 1
            if i < n:
                code_block.append(lines[i])
                i += 1
            output_lines.append("\n".join(code_block))
            continue

        # Check for Markdown Table
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?\s*[-:]+[-| :]*$", lines[i + 1]):
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < n and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            output_lines.append(convert_table(table_lines))
            continue

        # Check for Headings
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            heading_text = re.sub(r"\s+#+$", "", heading_text)
            clean_text = process_inline_markdown(heading_text)
            # Typst heading: = Level 1, == Level 2, === Level 3, etc.
            eqs = "=" * level
            output_lines.append(f"{eqs} {clean_text}")
            i += 1
            continue

        # Check for Blockquotes
        if line.strip().startswith(">"):
            quote_lines = []
            while i < n and (lines[i].strip().startswith(">") or (lines[i].strip() == "" and i + 1 < n and lines[i + 1].strip().startswith(">"))):
                quote_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            
            # Convert * list items inside quote to - so they don't break as unclosed bold
            clean_inner_lines = []
            for ql in quote_lines:
                ql = re.sub(r"^(\s*)\*\s+", r"\1- ", ql)
                clean_inner_lines.append(ql)

            inner_content = markdown_to_typst("\n".join(clean_inner_lines))
            output_lines.append(f"#quote(block: true)[\n{inner_content}\n]")
            continue

        # Check for Unordered Lists (- or *)
        list_match = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        if list_match:
            indent = list_match.group(1)
            item_text = process_inline_markdown(list_match.group(2))
            output_lines.append(f"{indent}- {item_text}")
            i += 1
            continue

        # Check for Ordered Lists (1. )
        num_list_match = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if num_list_match:
            indent = num_list_match.group(1)
            item_text = process_inline_markdown(num_list_match.group(2))
            output_lines.append(f"{indent}+ {item_text}")
            i += 1
            continue

        # Standard Paragraph line
        output_lines.append(process_inline_markdown(line))
        i += 1

    # Restore any remaining display math tokens
    result = "\n".join(output_lines)
    for idx, dmath in enumerate(display_math_tokens):
        result = result.replace(f"@@@DISPLAY_MATH_TOKEN_{idx}@@@", dmath)

    return result
