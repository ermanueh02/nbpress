"""
Processors for cell outputs: images (base64/svg), HTML tables (Pandas), and stdout/stderr/error text.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup

from nbpress.config import NbpressConfig
from nbpress.models import CellOutput, OutputType

# Regex to strip ANSI escape codes (terminal colors)
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from terminal outputs."""
    return ANSI_ESCAPE_RE.sub("", text)


def escape_typst_string(text: str) -> str:
    """Escape backslashes and double quotes for Typst strings."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def process_image_output(
    output: CellOutput,
    assets_dir: Path,
    image_counter: int,
) -> Optional[str]:
    """
    Save base64 or SVG image to assets_dir and return Typst image markup.
    """
    pair = output.image_mime_and_data
    if not pair:
        return None

    mime, data_str = pair
    assets_dir.mkdir(parents=True, exist_ok=True)

    if mime == "image/svg+xml":
        img_filename = f"output_img_{image_counter}.svg"
        img_path = assets_dir / img_filename
        # SVG might be raw XML or base64
        if data_str.strip().startswith("<svg") or "<?xml" in data_str:
            img_path.write_text(data_str, encoding="utf-8")
        else:
            try:
                decoded = base64.b64decode(data_str)
                img_path.write_bytes(decoded)
            except Exception:
                img_path.write_text(data_str, encoding="utf-8")
    else:
        ext = "png" if "png" in mime else ("jpg" if "jpeg" in mime else "webp")
        img_filename = f"output_img_{image_counter}.{ext}"
        img_path = assets_dir / img_filename
        # Strip data URI prefix if present
        clean_base64 = re.sub(r"^data:image\/[a-z]+;base64,", "", data_str.strip())
        decoded = base64.b64decode(clean_base64)
        img_path.write_bytes(decoded)

    # Return Typst relative image reference within the build directory
    return f'#nb-image("assets/{img_filename}")'


def process_html_table(html_content: str, eco: bool = False) -> str:
    """
    Convert a Pandas HTML table to a clean Typst #table(...) block.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")
    if not table:
        return ""

    rows_data = []
    # Extract headers (th)
    headers = []
    thead = table.find("thead")
    if thead:
        header_rows = thead.find_all("tr")
        for hr in header_rows:
            ths = hr.find_all(["th", "td"])
            row_ths = [th.get_text(strip=True) for th in ths]
            if row_ths:
                headers.append(row_ths)
    
    # Extract body rows
    tbody = table.find("tbody") or table
    body_rows = tbody.find_all("tr")
    for tr in body_rows:
        # Avoid re-adding thead rows if tbody wasn't explicitly found
        if thead and tr in thead.find_all("tr"):
            continue
        cells = tr.find_all(["td", "th"])
        row_cells = [c.get_text(strip=True) for c in cells]
        if row_cells:
            rows_data.append(row_cells)

    # Determine number of columns
    num_cols = 0
    if headers:
        num_cols = max(len(h) for h in headers)
    if rows_data:
        num_cols = max(num_cols, max(len(r) for r in rows_data))

    if num_cols == 0:
        return ""

    typst = [
        f"#nb-table(\n  columns: {num_cols},",
        f"  eco: {'true' if eco else 'false'},",
    ]

    # Add header cells
    if headers:
        for hr in headers:
            for th in hr:
                clean_th = escape_typst_string(th)
                typst.append(f'  [* {clean_th} *],')
    
    # Add data cells
    for row in rows_data:
        for c in row:
            clean_c = escape_typst_string(c)
            typst.append(f'  [{clean_c}],')

    typst.append(")")
    return "\n".join(typst)


def process_stream_output(text: str, max_lines: int = 35) -> str:
    """
    Format standard output/error text, with ANSI stripping and line truncation.
    """
    clean_text = strip_ansi(text).rstrip()
    if not clean_text:
        return ""

    # Suppress uninformative graphical object representations (e.g., <Axes: >, [<matplotlib.lines...>])
    if re.match(r"^(<matplotlib\.[^>]+>|<Axes[^>]*>|\[<matplotlib\.[^>]+>\]|<Figure size [^>]+>)$", clean_text.strip()):
        return ""

    lines = clean_text.splitlines()
    omitted_count = 0
    if len(lines) > max_lines:
        omitted_count = len(lines) - max_lines
        lines = lines[:max_lines]

    truncated_content = "\n".join(lines)
    # Escape triple backticks
    safe_content = truncated_content.replace("```", r"\`\`\`")

    return f"""
#nb-stdout(
  ```text
{safe_content}
```,
  omitted_lines: {omitted_count},
)
""".strip()


def process_error_output(output: CellOutput) -> str:
    """
    Format Python exception/error traceback cleanly.
    """
    ename = output.ename or "Error"
    evalue = output.evalue or ""
    traceback_lines = output.traceback or []
    clean_tb = strip_ansi("\n".join(traceback_lines)).strip()
    safe_tb = clean_tb.replace("```", r"\`\`\`")

    return f"""
#nb-error(
  ename: "{escape_typst_string(ename)}",
  evalue: "{escape_typst_string(evalue)}",
  traceback: ```text
{safe_tb}
```,
)
""".strip()


def format_outputs(
    outputs: List[CellOutput],
    assets_dir: Path,
    config: NbpressConfig,
    cell_idx: int,
) -> List[str]:
    """
    Format all outputs of a cell into Typst code snippets.
    """
    rendered_outputs: List[str] = []
    img_subcounter = 0

    for out in outputs:
        # 1. Images (highest priority for visual plots)
        if out.has_image:
            img_code = process_image_output(
                out,
                assets_dir=assets_dir,
                image_counter=cell_idx * 100 + img_subcounter,
            )
            if img_code:
                rendered_outputs.append(img_code)
                img_subcounter += 1
            continue

        # 2. HTML Tables (Pandas DataFrames)
        if out.has_html_table:
            html = out.data.get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            table_code = process_html_table(html, eco=config.eco)
            if table_code:
                rendered_outputs.append(table_code)
            continue

        # 3. Plain text / streams (stdout, stderr, text/plain)
        if out.output_type == OutputType.STREAM and out.text:
            stream_code = process_stream_output(out.text, max_lines=config.max_output_lines)
            if stream_code:
                rendered_outputs.append(stream_code)
            continue

        if out.output_type in (OutputType.EXECUTE_RESULT, OutputType.DISPLAY_DATA):
            if "text/plain" in out.data:
                plain_text = out.data["text/plain"]
                if isinstance(plain_text, list):
                    plain_text = "".join(plain_text)
                plain_code = process_stream_output(plain_text, max_lines=config.max_output_lines)
                if plain_code:
                    rendered_outputs.append(plain_code)
                continue

        # 4. Error tracebacks
        if out.output_type == OutputType.ERROR:
            error_code = process_error_output(out)
            if error_code:
                rendered_outputs.append(error_code)
            continue

    return rendered_outputs
