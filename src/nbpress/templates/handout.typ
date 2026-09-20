// Handout Layout (Slide-Printer for study and lecture notes)
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
  header: text(size: 8pt, fill: colors.muted)[
    #grid(
      columns: (1fr, 1fr),
      align(left)[_{{ title }}_],
      align(right)[nbpress {{ theme }} handout],
    )
    #v(-4pt)
    #line(length: 100%, stroke: 0.4pt + colors.divider)
  ],
  footer: context {
    align(center, text(size: 8.5pt, fill: colors.muted)[
      Diapositiva #counter(page).display("1") de #counter(page).final().first()
    ])
  }
)

#set text(
  font: if "{{ theme }}" == "mid-century" { ("Liberation Sans", "DejaVu Sans", "Helvetica", "Arial") } else { ("DejaVu Sans", "Arial", "Helvetica") },
  size: 9.5pt,
  fill: colors.dark,
  lang: "{{ language }}",
)

{% for slide in slides %}
// --- SLIDE {{ loop.index }} ---
#block(
  width: 100%,
  stroke: 0.75pt + colors.border,
  radius: 6pt,
  fill: colors.bg-card,
  inset: 12pt,
  [
    #grid(
      columns: (1fr, auto),
      [
        #text(size: 13pt, weight: "bold", fill: colors.primary)[{{ slide.title }}]
      ],
      [
        #box(
          fill: colors.badge-bg,
          radius: 3pt,
          inset: (x: 6pt, y: 3pt),
          text(size: 8pt, weight: "bold", fill: colors.badge-fg)[Slide {{ loop.index }}]
        )
      ]
    )
    #v(4pt)
    #line(length: 100%, stroke: 0.5pt + colors.divider)
    #v(8pt)

    {{ slide.content }}
  ]
)

#v(14pt)

// --- ZONA DE APUNTES MANUSCRITOS ---
{% if grid_style == "dots" %}
#dot-grid(height: 195pt, dot-color: colors.border)
{% elif grid_style == "grid" %}
#note-grid(height: 195pt, grid-color: colors.border)
{% elif grid_style == "blank" %}
#blank-notes(height: 195pt, stroke-color: colors.border)
{% else %}
#note-lines(count: {{ note_lines }}, stroke-color: colors.border)
{% endif %}

{% if not loop.last %}
#pagebreak()
{% endif %}
{% endfor %}
