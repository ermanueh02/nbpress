"""
Tests for Markdown to Typst conversion.
"""

from nbpress.processors.markdown import convert_table, markdown_to_typst, process_inline_markdown


def test_process_inline_markdown():
    # Bold and Italic
    assert "*importante*" in process_inline_markdown("**importante**")
    assert "_destacado_" in process_inline_markdown("*destacado*")

    # Links
    link_md = "[Google](https://google.com)"
    typst_link = process_inline_markdown(link_md)
    assert '#link("https://google.com")[Google]' == typst_link

    # Inline math preservation
    math_md = "Sea $x > 0$ y $y = \\alpha + \\beta$."
    res = process_inline_markdown(math_md)
    assert "$x > 0$" in res
    assert "$y = alpha + beta$" in res


def test_markdown_to_typst_headings():
    source = """# Titulo Principal
## Subseccion 1
### Detalle Nivel 3"""
    typ = markdown_to_typst(source)
    assert "= Titulo Principal" in typ
    assert "== Subseccion 1" in typ
    assert "=== Detalle Nivel 3" in typ


def test_convert_table():
    lines = [
        "| Columna 1 | Columna 2 |",
        "| :--- | :--- |",
        "| Valor A | Valor B |",
    ]
    table_typ = convert_table(lines)
    assert "#table(" in table_typ
    assert "columns: 2" in table_typ
    assert "[* Columna 1 *]" in table_typ
    assert "[Valor A]" in table_typ
