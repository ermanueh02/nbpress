// Slides Layout (16:9 Landscape Widescreen Presentation Deck)
#import "base.typ": *

#let colors = get-theme-colors(theme-name: "{{ theme }}", eco: {{ 'true' if eco else 'false' }})

#let nb-image(
  path,
  caption: none,
  width: 100%,
  max-height: 8.2cm,
  fit: "contain",
) = {
  align(center + horizon, block(
    breakable: false,
    inset: 2pt,
    [
      #image(path, width: width, height: max-height, fit: fit)
      #if caption != none [
        #v(2pt)
        #text(size: 8pt, fill: rgb("6c757d"), style: "italic")[#caption]
      ]
    ]
  ))
}

#let nb-table(
  columns: 2,
  eco: false,
  theme: "{{ theme }}",
  ..cells
) = {
  let colors = get-theme-colors(theme-name: theme, eco: eco)
  let header-bg = if eco { rgb("ffffff") } else if theme == "mid-century" { rgb("f2ebe0") } else { rgb("f1f3f5") }
  let even-bg = if eco { rgb("ffffff") } else if theme == "mid-century" { rgb("fbf9f4") } else { rgb("fafbfc") }
  let border = if eco { 0.7pt + rgb("000000") } else { 0.5pt + colors.border }

  align(center, block(
    breakable: false,
    text(size: 8pt)[
      #table(
        columns: columns,
        stroke: (col, row) => if row == 0 { (bottom: 1.5pt + colors.primary) } else { border },
        fill: (col, row) => if row == 0 { header-bg } else if calc.even(row) { even-bg } else { none },
        inset: (x: 4pt, y: 3pt),
        align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
        ..cells
      )
    ]
  ))
}

#set page(
  paper: "presentation-16-9",
  fill: colors.bg-page,
  margin: (
    top: 1.6cm,
    bottom: 1.4cm,
    left: 1.8cm,
    right: 1.8cm,
  ),
  header: context {
    let page_num = counter(page).get().first()
    let total_pages = counter(page).final().first()
    if page_num > 1 {
      text(size: 9.5pt, fill: colors.muted)[
        #grid(
          columns: (1fr, auto),
          align(left)[*{{ title }}*],
          align(right)[Diapositiva #page_num de #total_pages],
        )
        #v(-4pt)
        #line(length: 100%, stroke: 0.4pt + colors.divider)
      ]
    }
  },
  footer: text(size: 8.5pt, fill: colors.muted)[
    #line(length: 100%, stroke: 0.3pt + colors.divider)
    #v(3pt)
    #grid(
      columns: (1fr, 1fr),
      align(left)[
        {% if authors %}
        {{ authors | join(", ") }}
        {% endif %}
      ],
      align(right)[nbpress {{ theme }} deck],
    )
  ]
)

#set text(
  font: if "{{ theme }}" == "mid-century" { ("Liberation Sans", "DejaVu Sans", "Helvetica", "Arial") } else { ("DejaVu Sans", "Arial", "Liberation Sans") },
  size: 13pt,
  fill: colors.dark,
  lang: "{{ language }}",
)

#set par(justify: false, leading: 0.65em)

{% for slide in slides %}
{% if loop.first and cover %}
// --- DIAPOSITIVA DE PORTADA ---
#align(center + horizon)[
  #block(
    width: 90%,
    stroke: 1.5pt + colors.primary,
    radius: 8pt,
    fill: colors.bg-card,
    inset: (x: 24pt, y: 28pt),
    [
      {% if theme == "mid-century" %}
      #box(
        fill: colors.badge-bg,
        radius: 4pt,
        inset: (x: 8pt, y: 4pt),
        text(size: 9pt, weight: "bold", fill: colors.badge-fg, tracking: 1.5pt)[MID-CENTURY • DECK]
      )
      #v(10pt)
      {% endif %}

      #text(size: 26pt, weight: "bold", fill: colors.dark)[{{ title }}]
      
      {% if subtitle %}
      #v(10pt)
      #text(size: 15pt, style: "italic", fill: colors.muted)[{{ subtitle }}]
      {% endif %}

      #v(16pt)
      #line(length: 30%, stroke: 2pt + colors.secondary)
      #v(16pt)

      {% if authors %}
      #text(size: 13.5pt, weight: "medium", fill: colors.dark)[
        {{ authors | join("   |   ") }}
      ]
      #v(8pt)
      {% endif %}

      {% if date %}
      #text(size: 11pt, fill: colors.muted)[{{ date }}]
      {% endif %}
    ]
  )
]
#pagebreak()
{% endif %}

// --- SLIDE {{ loop.index }} ---
#grid(
  columns: (1fr, auto),
  align(left + bottom)[
    #text(size: 19pt, weight: "bold", fill: colors.primary)[{{ slide.title }}]
  ],
  align(right + bottom)[
    #box(
      fill: colors.badge-bg,
      radius: 4pt,
      inset: (x: 8pt, y: 4pt),
      text(size: 9.5pt, weight: "bold", fill: colors.badge-fg)[Slide {{ loop.index }}]
    )
  ]
)
#v(4pt)
#line(length: 100%, stroke: 1.2pt + colors.secondary)
#v(10pt)

#set text(size: 11.5pt)
{{ slide.content }}

{% if not loop.last %}
#pagebreak()
{% endif %}
{% endfor %}
