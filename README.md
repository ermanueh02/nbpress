# nbpress 📖✨

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/nbpress/)
[![Typst Engine](https://img.shields.io/badge/engine-Typst%200.14%2B-239dad)](https://typst.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Web Studio](https://img.shields.io/badge/Web%20Studio-100%25%20In--Browser%20%C2%B7%20PWA-ea580c)](https://ermanueh02.github.io/nbpress/)

> Transform Jupyter Notebooks (`.ipynb`) into editorial-grade, print-ready PDFs, presentation slides, Slide-Printer handouts, and compact revision sheets.

`nbpress` is a modern, high-precision publishing tool for Jupyter Notebooks. It bridges computational data science and editorial graphic design, converting `.ipynb` files into publication-quality PDF documents with balanced margins, running headers, ligatures, math formulas, and customizable note-taking areas for printing.

Powered by the lightning-fast, native **Typst** typesetting engine and inspired by **Slide-Printer**'s Swiss / Mid-Century Modern design system.

---

## 🌐 Web Studio & PWA (100% In-Browser)

Launch the offline browser studio directly from your terminal:

```bash
nbpress --web
# or explicitly specify port:
nbpress web --port 8000
```

- **100% Private & In-Browser**: Your notebooks are parsed directly in browser memory. Zero files are uploaded to any server.
- **Multi-Page Live Preview**: Inspect your sheets before compiling, with realistic paper drop shadows, binding gutters, hole punch guides, and pagination.
- **Direct Browser Print-to-PDF**: Formatted with exact `@media print` rules for DIN A4 and US Letter with 0 browser margin distortion.
- **Multilingual (EN / ES / GL)**: Real-time interface translation between English, Español, and Galego.
- **PWA Ready**: Works offline, installable as a standalone desktop/mobile application.
- **CLI Command Generator**: Dynamically generates the exact `nbpress build ...` command as you tweak settings in the UI.

---

## ✨ Key Features

- **Editorial Quality**: Professional typography, ligatures, LaTeX physics & math formulas, balanced margins, and page counters (`Page X of Y`).
- **4 Purpose-Built Layout Modes**:
  - 📄 **`document`** (Continuous Report / Academic): Includes optional cover page, automatic Table of Contents (TOC), section headers, and running footers.
  - 🖥️ **`slides`** (Presentation Deck): Modern 16:9 widescreen landscape presentation slides with cover slide and section badges.
  - 📝 **`handout`** (Slide-Printer): Renders slides in the top half and provides a lined, grid, or dot-grid notes area in the bottom half for handwritten lecture notes (1-up or 2-up).
  - ⚡ **`cheatsheet`** (Compact Summary): Dense 2-column layout optimized for quick reference and saving paper.
- **Smart Print Optimization**:
  - 🖨️ **Gutter Margin**: Configurable inside margin (e.g. `1.5cm`, `--gutter binder` +11mm, `--spiral` +8mm) for ring binders and spiral coils.
  - 🔄 **Duplex Support (`--duplex`)**: Alternates binding margins between recto (odd) and verso (even) sheets so punched holes never bite into content.
  - 🎯 **Hole Guides (`--hole-guides`)**: Subtle ISO 838 crosshairs for clean 2/4-hole punching.
  - 🌱 **Eco / Ink-Saver Mode (`--eco`)**: Light backgrounds for code blocks and high-contrast styling to save toner and ink.
  - ✂️ **Smart Page Breaks**: Avoids cutting code blocks, tables, or charts across page boundaries (`page-break-inside: avoid`).
- **Rich Output & Media Management**:
  - High-res embedded charts and local figures (`![alt](imgs/...)` & `<img src="...">`).
  - Automatic image format sanitization (GIF to PNG, JPEG signature repair).
  - Clean typographic tables for Pandas DataFrames and GFM Markdown tables.
  - Comprehensive LaTeX physics and math engine (Bethe-Bloch, Dirac, cross-sections, matrices, isotopes, integrals).
  - Configurable truncation for long stdout/stderr terminal outputs.
- **Multi-Modal Experience**:
  - **Offline Web Studio**: `nbpress --web`
  - **Interactive Guided Terminal Wizard**: `nbpress wizard`
  - **High-Throughput CLI Batch Processing**: `nbpress build ...`
  - **Instant System Preview**: `nbpress preview ...`

---

## 🚀 Quick Start

### Installation

```bash
pip install nbpress
```

*(Slide-printer integration is automatically resolved from git).*

---

### Interactive Guided Wizard 🧙

Launch the terminal wizard simply by running:

```bash
nbpress
# or
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
# Launch the offline Web Studio in your browser
nbpress --web

# Compile a notebook into an editorial document
nbpress build analysis.ipynb -o report.pdf

# Compile multiple architectures at once (e.g. document + slides + handout)
nbpress build analysis.ipynb --layout document,slides,handout

# Compile all 4 architectures simultaneously in one command
nbpress build analysis.ipynb --all-layouts

# Use the elegant Mid-Century Modern theme (ochre, terracotta, sage olive, ivory)
nbpress build analysis.ipynb --theme mid-century --all-layouts

# Generate a slide handout with technical graph grid notes (Slide-Printer API)
nbpress build lecture.ipynb --layout handout --handout-style grid

# Generate a compact 2-Up handout with dot-grid bullet notes
nbpress build lecture.ipynb --layout handout --handout-style dots --handout-layout 2-up

# Create a 2-column compact cheatsheet in Eco/Ink-Saver mode
nbpress build machine_learning.ipynb -o summary.pdf --layout cheatsheet --eco

# Inspect notebook metadata, cell counts, outputs, and slide markers
nbpress info analysis.ipynb

# Preview directly in default system PDF viewer
nbpress preview analysis.ipynb --layout handout --theme mid-century
```

---

## 🛠️ CLI Reference Table

| Option / Command | Description | Default |
| :--- | :--- | :--- |
| `nbpress --web` / `nbpress web` | Launch the offline local Web Studio in browser | Port `8000` |
| `nbpress wizard` | Launch interactive guided terminal wizard | — |
| `nbpress build <file.ipynb>` | Compile notebook to PDF | — |
| `-l`, `--layout` | `document`, `slides`, `handout`, `cheatsheet`, `all` | `document` |
| `--all-layouts` | Compile all 4 layouts in parallel | `false` |
| `-t`, `--theme` | Visual theme: `editorial`, `mid-century`, `minimal` | `editorial` |
| `-p`, `--paper` | Paper format: `a4`, `us-letter`, `a5` | `a4` |
| `--handout-style` | Note pattern: `lines`, `grid`, `dots`, `blank` | `lines` |
| `--handout-layout`| Slide arrangement: `1-up`, `2-up` | `1-up` |
| `--gutter` | Inside binding margin (e.g. `1.5cm`) | `None` |
| `--duplex` | Alternate binding margin for recto/verso pages | `false` |
| `--eco` | Ink-saver mode for monochrome printing | `false` |
| `--keep-typ` | Preserve generated `.typ` source file | `false` |
| `nbpress preview <file>` | Compile and open immediately in system PDF viewer | — |
| `nbpress info <file>` | Detailed cell, table, chart, and slide statistics | — |

---

## 📜 License

MIT License © 2026 nbpress contributors.
