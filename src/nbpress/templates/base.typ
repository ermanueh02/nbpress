// nbpress base styles and macros

#let get-theme-colors(theme-name: "editorial", eco: false) = {
  if theme-name == "mid-century" {
    (
      bg-page: if eco { rgb("ffffff") } else { rgb("fbf9f5") },
      bg-card: if eco { rgb("ffffff") } else { rgb("f7f4eb") },
      bg-code: if eco { rgb("ffffff") } else { rgb("f4efe6") },
      primary: rgb("c85a32"),       // Terracotta / Burnt Sienna
      secondary: rgb("d49b24"),     // Mustard Ochre
      accent: rgb("3d5a4c"),        // Olive Forest Sage
      dark: rgb("24201d"),          // Dark Teak / Walnut
      muted: rgb("766d66"),         // Warm Muted Gray
      border: if eco { rgb("766d66") } else { rgb("e2ddd2") },
      divider: rgb("d8cebd"),
      badge-bg: rgb("faebd7"),
      badge-fg: rgb("c85a32"),
    )
  } else {
    (
      bg-page: rgb("ffffff"),
      bg-card: if eco { rgb("ffffff") } else { rgb("f8f9fa") },
      bg-code: if eco { rgb("ffffff") } else { rgb("f8f9fa") },
      primary: rgb("0d6efd"),       // Classic Blue
      secondary: rgb("0a58ca"),
      accent: rgb("0dcaf0"),
      dark: rgb("212529"),
      muted: rgb("6c757d"),
      border: if eco { rgb("495057") } else { rgb("dee2e6") },
      divider: rgb("e9ecef"),
      badge-bg: rgb("e7f1ff"),
      badge-fg: rgb("0d6efd"),
    )
  }
}

#let nb-code-cell(
  body,
  prompt: "In [ ]",
  show_prompt: true,
  eco: false,
  line_numbers: true,
  theme: "editorial",
) = {
  let colors = get-theme-colors(theme-name: theme, eco: eco)
  let bg-color = colors.bg-code
  let border-color = colors.border
  let prompt-color = colors.muted

  block(
    width: 100%,
    breakable: false,
    radius: 4pt,
    stroke: (
      left: if eco { 2pt + border-color } else { 3pt + colors.primary },
      rest: 0.5pt + border-color,
    ),
    fill: bg-color,
    inset: (x: 8pt, y: 7pt),
    outset: 0pt,
    [
      #if show_prompt [
        #place(
          top + right,
          text(size: 7.5pt, fill: prompt-color, font: "DejaVu Sans Mono", weight: "bold", prompt)
        )
      ]
      #set text(size: 8.5pt, fill: colors.dark)
      #body
    ]
  )
}

#let nb-stdout(
  body,
  omitted_lines: 0,
  theme: "editorial",
) = {
  let colors = get-theme-colors(theme-name: theme, eco: false)
  block(
    width: 100%,
    breakable: false,
    radius: 3pt,
    stroke: 0.5pt + colors.border,
    fill: if theme == "mid-century" { rgb("faf8f3") } else { rgb("fbfcfd") },
    inset: (x: 8pt, y: 6pt),
    [
      #set text(size: 8pt, fill: colors.dark, font: "DejaVu Sans Mono")
      #body
      #if omitted_lines > 0 [
        #v(3pt)
        #align(center, text(size: 7.5pt, fill: colors.muted, style: "italic")[
          --- [... #omitted_lines líneas omitidas para optimizar espacio ...] ---
        ])
      ]
    ]
  )
}

#let nb-error(
  ename: "Error",
  evalue: "",
  traceback: none,
) = {
  block(
    width: 100%,
    breakable: false,
    radius: 3pt,
    stroke: 1pt + rgb("e03131"),
    fill: rgb("fff5f5"),
    inset: (x: 8pt, y: 7pt),
    [
      #text(size: 8.5pt, weight: "bold", fill: rgb("c92a2a"))[#ename: #evalue]
      #if traceback != none [
        #v(4pt)
        #set text(size: 7.5pt, fill: rgb("495057"), font: "DejaVu Sans Mono")
        #traceback
      ]
    ]
  )
}

#let nb-image(
  path,
  caption: none,
  width: 92%,
) = {
  align(center, block(
    breakable: false,
    inset: 4pt,
    [
      #image(path, width: width)
      #if caption != none [
        #v(3pt)
        #text(size: 8pt, fill: rgb("6c757d"), style: "italic")[#caption]
      ]
    ]
  ))
}

#let nb-table(
  columns: 2,
  eco: false,
  theme: "editorial",
  ..cells
) = {
  let colors = get-theme-colors(theme-name: theme, eco: eco)
  let header-bg = if eco { rgb("ffffff") } else if theme == "mid-century" { rgb("f2ebe0") } else { rgb("f1f3f5") }
  let even-bg = if eco { rgb("ffffff") } else if theme == "mid-century" { rgb("fbf9f4") } else { rgb("fafbfc") }
  let border = if eco { 0.7pt + rgb("000000") } else { 0.5pt + colors.border }

  align(center, block(
    breakable: false,
    table(
      columns: columns,
      stroke: (col, row) => if row == 0 { (bottom: 1.5pt + colors.primary) } else { border },
      fill: (col, row) => if row == 0 { header-bg } else if calc.even(row) { even-bg } else { none },
      inset: (x: 6pt, y: 4.5pt),
      align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
      ..cells
    )
  ))
}

#let note-lines(count: 8, stroke-color: rgb("ced4da"), label: "NOTAS / APUNTES") = {
  let lines = ()
  for i in range(count) {
    lines.push(line(length: 100%, stroke: 0.5pt + stroke-color))
    lines.push(v(16pt))
  }
  block(
    width: 100%,
    [
      #v(6pt)
      #text(size: 8pt, fill: rgb("868e96"), weight: "bold", tracking: 1.2pt)[#label]
      #v(10pt)
      #for el in lines { el }
    ]
  )
}

#let note-grid(height: 190pt, spacing: 14pt, grid-color: rgb("dee2e6"), label: "ÁREA DE APUNTES (CUADRÍCULA)") = {
  block(
    width: 100%,
    height: height,
    stroke: 0.5pt + grid-color,
    radius: 4pt,
    fill: rgb("ffffff"),
    inset: 8pt,
    [
      #text(size: 8pt, fill: rgb("868e96"), weight: "bold", tracking: 1.2pt)[#label]
      #v(6pt)
      #pattern(size: (spacing, spacing))[
        #place(top + left, line(length: 100%, stroke: 0.35pt + grid-color))
        #place(top + left, line(start: (0pt, 0pt), end: (0pt, spacing), stroke: 0.35pt + grid-color))
      ]
    ]
  )
}

#let dot-grid(height: 190pt, spacing: 14pt, dot-color: rgb("adb5bd"), label: "ÁREA DE APUNTES (PUNTOS / BULLETS)") = {
  block(
    width: 100%,
    height: height,
    stroke: 0.5pt + rgb("e9ecef"),
    radius: 4pt,
    fill: rgb("ffffff"),
    inset: 8pt,
    [
      #text(size: 8pt, fill: rgb("868e96"), weight: "bold", tracking: 1.2pt)[#label]
      #v(8pt)
      #pattern(size: (spacing, spacing))[
        #place(top + left, circle(radius: 0.75pt, fill: dot-color))
      ]
    ]
  )
}

#let blank-notes(height: 190pt, stroke-color: rgb("ced4da"), label: "ÁREA DE APUNTES") = {
  block(
    width: 100%,
    height: height,
    stroke: 0.5pt + stroke-color,
    radius: 4pt,
    fill: rgb("ffffff"),
    inset: 10pt,
    [
      #text(size: 8pt, fill: rgb("868e96"), weight: "bold", tracking: 1.2pt)[#label]
    ]
  )
}

#let nb-slide-card(
  title,
  body,
  slide_num: 1,
  theme: "editorial",
) = {
  let colors = get-theme-colors(theme-name: theme, eco: false)
  block(
    width: 100%,
    stroke: 0.75pt + colors.border,
    radius: 6pt,
    fill: colors.bg-card,
    inset: 12pt,
    [
      #grid(
        columns: (1fr, auto),
        [
          #text(size: 13pt, weight: "bold", fill: colors.primary)[#title]
        ],
        [
          #box(
            fill: colors.badge-bg,
            radius: 3pt,
            inset: (x: 6pt, y: 3pt),
            text(size: 8pt, weight: "bold", fill: colors.badge-fg)[Slide #slide_num]
          )
        ]
      )
      #v(4pt)
      #line(length: 100%, stroke: 0.5pt + colors.divider)
      #v(8pt)
      #body
    ]
  )
}
