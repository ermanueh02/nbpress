"""
Code cell formatting for Typst.
"""

from __future__ import annotations

from typing import Optional
from nbpress.config import NbpressConfig
from nbpress.models import NotebookCell


def format_code_cell(cell: NotebookCell, config: NbpressConfig, language: str = "python") -> str:
    """
    Format a code cell into a styled Typst block with syntax highlighting,
    optional line numbers, and an execution count badge.
    """
    source = cell.source.strip()
    if not source:
        return ""

    # Execution count badge
    count_str = f"In [{cell.execution_count if cell.execution_count is not None else ' '}]"
    
    # Escape triple backticks if any
    safe_source = source.replace("```", r"\`\`\`")

    # Call custom Typst macro defined in templates/base.typ
    # #nb-code-cell(source, lang: "python", prompt: "In [1]", eco: false, line_numbers: true)
    eco_val = "true" if config.eco else "false"
    show_prompts_val = "true" if config.show_prompts else "false"
    line_numbers_val = "true" if config.line_numbers else "false"

    typst_block = f"""
#nb-code-cell(
  ```{language}
{safe_source}
```,
  prompt: "{count_str}",
  show_prompt: {show_prompts_val},
  eco: {eco_val},
  line_numbers: {line_numbers_val},
)
"""
    return typst_block.strip()
