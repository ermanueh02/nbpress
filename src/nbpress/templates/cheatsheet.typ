// Cheatsheet Layout (Compact 2-column quick reference guide)
#import "base.typ": *

#let colors = get-theme-colors(theme-name: "{{ theme }}", eco: {{ 'true' if eco else 'false' }})

#set page(
  paper: "{{ paper }}",
  fill: colors.bg-page,
  columns: 2,
  margin: (
    top: 1.2cm,
    bottom: 1.2cm,
    inside: 1.2cm,
    outside: 1.2cm,
  ),
  header: text(size: 7.5pt, fill: colors.muted)[
    #grid(
      columns: (1fr, 1fr),
      align(left)[*{{ title }}* --- _Guía Rápida / Resumen_],
      align(right)[nbpress {{ theme }} cheatsheet],
    )
    #v(-4pt)
    #line(length: 100%, stroke: 0.4pt + colors.divider)
  ],
  footer: context {
    align(center, text(size: 7.5pt, fill: colors.muted)[
      Pág. #counter(page).display("1") de #counter(page).final().first()
    ])
  }
)

#set text(
  font: if "{{ theme }}" == "mid-century" { ("Liberation Sans", "DejaVu Sans", "Helvetica", "Arial") } else { ("DejaVu Sans", "Arial", "Liberation Sans") },
  size: 8pt,
  fill: colors.dark,
  lang: "{{ language }}",
)

#set par(justify: true, leading: 0.45em)
#set heading(numbering: none)

// Cabecera compacta
#place(top, scope: "parent", float: true)[
  #block(
    width: 100%,
    fill: colors.bg-card,
    stroke: 0.5pt + colors.border,
    radius: 3pt,
    inset: (x: 8pt, y: 5pt),
    [
      #grid(
        columns: (1fr, auto),
        [
          #text(size: 11pt, weight: "bold", fill: colors.dark)[{{ title }}]
          {% if authors %}
          #h(8pt) #text(size: 8pt, fill: colors.muted)[{{ authors | join(", ") }}]
          {% endif %}
        ],
        [
          #text(size: 7.5pt, fill: colors.primary, weight: "bold", tracking: 1pt)[RESUMEN RÁPIDO]
        ]
      )
    ]
  )
  #v(6pt)
]

// Elementos compactos a 2 columnas
{% for item in rendered_items %}
#block(
  width: 100%,
  breakable: false,
  [
    {{ item }}
  ]
)
#v(6pt)
{% endfor %}
