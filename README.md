# nbpress 📖✨

> Transform Jupyter Notebooks (`.ipynb`) into editorial-grade, print-ready PDFs and handouts.

`nbpress` is a modern Python tool designed to convert your Jupyter Notebooks into clean, structured, and beautifully typeset PDF documents ready for printing (A4 / Letter), academic reporting, slide handouts, and compact revision sheets.

Powered by the lightning-fast, high-precision **Typst** typesetting engine.

---

## ✨ Features

- **Editorial Quality**: Professional typography, ligatures, math formulas, balanced margins, and page counters (`Page X of Y`).
- **4 Purpose-Built Layout Modes**:
  - 📄 **`document`** (Continuous Report / Academic): Includes optional cover page, automatic Table of Contents (TOC), section headers, and running footers.
  - 🖥️ **`slides`** (Presentation Deck): Modern 16:9 widescreen landscape presentation slides with cover slide and section badges.
  - 📝 **`handout`** (Slide-Printer): Renders slides in the top half and provides a lined/dot-grid notes area in the bottom half for handwritten lecture notes.
  - ⚡ **`cheatsheet`** (Compact Summary): Dense 2-column layout optimized for quick reference and saving paper.
- **Smart Print Optimization**:
  - 🖨️ **Gutter Margin**: Configurable inside margin (e.g. `1.5cm`) for ring binders or spiral binding.
  - 🌱 **Eco / Ink-Saver Mode**: Light backgrounds for code blocks and high-contrast styling to save toner and ink.
  - ✂️ **Smart Page Breaks**: Avoids cutting code blocks, tables, or charts across page boundaries (`page-break-inside: avoid`).
- **Rich Output & Media Management**:
  - High-res embedded charts and local figures (`![alt](imgs/...)` & `<img src="...">`).
  - Automatic image format sanitization (GIF to PNG, JPEG signature repair).
  - Clean typographic tables for Pandas DataFrames and GFM Markdown tables.
  - Comprehensive LaTeX physics and math engine (Bethe-Bloch, Dirac, cross-sections, matrices, isotopes, integrals).
  - Configurable truncation for long stdout/stderr terminal outputs.
- **100% Self-Contained**: No external GTK/Pango/Cairo DLL dependencies. Works natively on Windows, macOS, and Linux out of the box.

---

## 🚀 Quick Start

### Installation

```bash
pip install nbpress
# slide-printer requirement is resolved automatically from git:
# git+https://github.com/ermanueh02/Slide-printer.git
```

### Interactive Slide-Printer Wizard 4.2.0 🧙

Launch the interactive guided terminal wizard simply by running:

```bash
nbpress
# or explicitly
nbpress wizard
```

The wizard guides you through:
1. **Notebook Discovery**: Automatically detects notebooks in current and sub-directories or accepts manual drag-and-drop paths.
2. **Deep Inspection**: Displays title, cell statistics, figures, tables, and detected slide boundaries.
3. **Layout Selection**: Easily switch between `document`, `slides`, `handout` and `cheatsheet`.
4. **Print Geometry & Eco**: Select paper sizes (A4, Letter, A5), binding gutter (for spiral/ring binders), and ink-saving mode.
5. **Pre-Flight Manifest**: Live preview of compilation parameters before running.
6. **Native Typst Compilation**: Live status spinner and sub-second generation.
7. **Post-Build Actions**: Immediately open in default system PDF viewer, reveal in File Explorer, or convert another notebook.

---

### Command-Line Usage (Non-Interactive)

```bash
# Compile a notebook into an editorial document
nbpress build analysis.ipynb -o report.pdf

# Generate presentation slides (16:9 widescreen)
nbpress build lecture.ipynb -o presentation.pdf --layout slides

# Generate a slide handout with note lines
nbpress build presentation.ipynb -o handout.pdf --layout handout

# Create a 2-column compact cheatsheet in Eco/Ink-Saver mode
nbpress build machine_learning.ipynb -o summary.pdf --layout cheatsheet --eco

# Inspect notebook metadata, cell counts, outputs, and slide markers
nbpress info analysis.ipynb

# Preview directly in default PDF viewer
nbpress preview analysis.ipynb --layout handout
```

---

## 📜 License

MIT License.
