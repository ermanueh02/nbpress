// Document Layout (Editorial & Continuous Report)
#import "base.typ": *

#let colors = get-theme-colors(theme-name: "{{ theme }}", eco: {{ 'true' if eco else 'false' }})

#set page(
  paper: "{{ paper }}",
  fill: colors.bg-page,
  margin: (
    top: {{ margin_top }},
    bottom: {{ margin_bottom }},
    inside: {{ margin_inside }},
    outside: {{ margin_outside }},
  ),
  header: context {
    let page_num = counter(page).get().first()
    {% if cover %}
    if page_num > 1 {
      text(size: 8pt, fill: colors.muted)[
        #grid(
          columns: (1fr, 1fr),
          align(left)[_{{ title }}_],
          align(right)[nbpress {{ theme }}],
        )
        #v(-4pt)
        #line(length: 100%, stroke: 0.4pt + colors.divider)
      ]
    }
    {% else %}
    text(size: 8pt, fill: colors.muted)[
      #grid(
        columns: (1fr, 1fr),
        align(left)[_{{ title }}_],
        align(right)[nbpress {{ theme }}],
      )
      #v(-4pt)
      #line(length: 100%, stroke: 0.4pt + colors.divider)
    ]
    {% endif %}
  },
  footer: context {
    {% if page_numbers %}
    let page_num = counter(page).get().first()
    {% if cover %}
    if page_num > 1 {
      align(center, text(size: 8.5pt, fill: colors.muted)[
        Pág. #counter(page).display("1") de #counter(page).final().first()
      ])
    }
    {% else %}
    align(center, text(size: 8.5pt, fill: colors.muted)[
      Pág. #counter(page).display("1") de #counter(page).final().first()
    ])
    {% endif %}
    {% endif %}
  }
)

#set text(
  font: if "{{ theme }}" == "mid-century" { ("Liberation Sans", "DejaVu Sans", "Helvetica", "Arial") } else { ("Linux Libertine", "Times New Roman", "DejaVu Serif") },
  size: 10pt,
  fill: colors.dark,
  lang: "{{ language }}",
)

#set par(justify: true, leading: 0.65em)
#set heading(numbering: "1.1")

{% if cover %}
// --- PORTADA EDITORIAL / MID-CENTURY ---
#align(center + horizon)[
  #v(-2.5cm)

  {% if theme == "mid-century" %}
  #box(
    fill: colors.badge-bg,
    radius: 4pt,
    inset: (x: 10pt, y: 5pt),
    text(size: 8.5pt, weight: "bold", fill: colors.badge-fg, tracking: 2pt)[MID-CENTURY MODERN • REPORT]
  )
  #v(14pt)
  {% endif %}

  #text(size: 25pt, weight: "bold", fill: colors.dark)[{{ title }}]
  
  {% if subtitle %}
  #v(10pt)
  #text(size: 13pt, style: "italic", fill: colors.muted)[{{ subtitle }}]
  {% endif %}

  #v(18pt)
  #line(length: 35%, stroke: 1.5pt + colors.primary)
  #v(18pt)

  {% if authors %}
  #text(size: 11pt, weight: "medium", fill: colors.dark)[
    {{ authors | join(", ") }}
  ]
  #v(6pt)
  {% endif %}

  {% if date %}
  #text(size: 9.5pt, fill: colors.muted)[{{ date }}]
  #v(15pt)
  {% endif %}

  {% if abstract %}
  #v(20pt)
  #align(center)[
    #block(
      width: 82%,
      fill: colors.bg-card,
      radius: 4pt,
      stroke: 0.5pt + colors.border,
      inset: 12pt,
      align(left)[
        #text(size: 8.5pt, weight: "bold", fill: colors.primary, tracking: 1.2pt)[RESUMEN / ABSTRACT]
        #v(4pt)
        #text(size: 9pt, style: "italic", fill: colors.dark)[{{ abstract }}]
      ]
    )
  ]
  {% endif %}
]

#pagebreak()
{% endif %}

{% if not cover %}
// Título en cabecera si no hay portada
#v(0.5cm)
#align(left)[
  #text(size: 20pt, weight: "bold", fill: colors.dark)[{{ title }}]
  {% if authors %}
  #v(4pt)
  #text(size: 10pt, fill: colors.muted)[{{ authors | join(", ") }}]
  {% endif %}
  #v(6pt)
  #line(length: 100%, stroke: 1.2pt + colors.primary)
]
#v(12pt)
{% endif %}

{% if toc %}
// --- ÍNDICE DE CONTENIDOS ---
#outline(
  title: [Índice de Contenidos],
  indent: auto,
)
#v(20pt)
{% if cover %}
#pagebreak()
{% endif %}
{% endif %}

// --- CUERPO DEL NOTEBOOK ---
{% for item in rendered_items %}
{{ item }}
#v(10pt)
{% endfor %}
